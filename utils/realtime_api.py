import asyncio
import json
import websockets
import time
import subprocess
import time
from loguru import logger
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Any, Callable, Coroutine, Dict
from pydantic import BaseModel, Field, SecretStr, PrivateAttr
from langchain_core.tools import BaseTool
from langchain_core._api import beta
from langchain_core.utils import secret_from_env
import sys
import io

from utils.websocket_utils import amerge
from intents import TOOLS
from utils import PIXEL_RING_PATH, Speaker

DEFAULT_MODEL = "gpt-4o-realtime-preview-2024-10-01"
DEFAULT_URL = "wss://api.openai.com/v1/realtime"

EVENTS_TO_IGNORE = {
    "response.function_call_arguments.delta",
    "rate_limits.updated",
    "response.audio_transcript.delta",
    "response.content_part.added",
    "response.content_part.done",
    "conversation.item.created",
    "session.created",
    "session.updated",
    "response.output_item.done",
}


@asynccontextmanager
async def connect(*, api_key: str, model: str, url: str) -> AsyncGenerator[
    tuple[
        Callable[[dict[str, Any] | str], Coroutine[Any, Any, None]],
        AsyncIterator[dict[str, Any]],
    ],
    None,
]:
    """
    async with connect(model="gpt-4o-realtime-preview-2024-10-01") as (send_event, receive_stream):
        await send_event("Hello, world!")
        async for message in receive_stream:
            print(message)
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    url = url or DEFAULT_URL
    url += f"?model={model}"

    websocket = await websockets.connect(url, additional_headers=headers)

    try:
        async def send_event(event: dict[str, Any] | str) -> None:
            formatted_event = json.dumps(event) if isinstance(event, dict) else event
            await websocket.send(formatted_event)

        async def event_stream() -> AsyncIterator[dict[str, Any]]:
            async for raw_event in websocket:
                yield json.loads(raw_event)

        stream: AsyncIterator[dict[str, Any]] = event_stream()

        yield send_event, stream
    finally:
        await websocket.close()


class VoiceToolExecutor(BaseModel):
    """
    Can accept function calls and emits function call outputs to a stream.
    """

    tools_by_name: dict[str, BaseTool]
    _trigger_future: asyncio.Future = PrivateAttr(default_factory=asyncio.Future)
    _lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)
    _stop: bool = PrivateAttr(default=False)

    def stop(self) -> None:
        """Signal the output_iterator() to stop."""
        self._stop = True
        # If there's a future that’s still waiting to be triggered, set it to done:
        if not self._trigger_future.done():
            # Provide some dummy result so _trigger_future doesn't hang.
            self._trigger_future.set_result({})

    async def _trigger_func(self) -> dict:
        """Waits until a tool call is added and returns the tool call."""
        return await self._trigger_future

    async def add_tool_call(self, tool_call: dict) -> None:
        """
        Adds a new tool call. This is typically triggered when the model
        sends a function_call_arguments.done event with JSON specifying tool name and arguments.
        """
        async with self._lock:
            if self._trigger_future.done():
                # If there's already a pending call, handle it or raise an error as needed
                raise ValueError("Tool call adding is already in progress.")
            self._trigger_future.set_result(tool_call)

    async def _create_tool_call_task(self, tool_call: dict) -> asyncio.Task:
        tool = self.tools_by_name.get(tool_call["name"])
        if tool is None:
            # If the tool is not found, we yield an error event
            raise ValueError(
                f"Tool '{tool_call['name']}' not found. "
                f"Must be one of {list(self.tools_by_name.keys())}"
            )

        # Attempt to parse arguments from JSON
        try:
            args = json.loads(tool_call["arguments"])
        except json.JSONDecodeError:
            raise ValueError(
                f"Failed to parse arguments `{tool_call['arguments']}`. Must be valid JSON."
            )

        async def run_tool() -> dict:
            result = await tool.ainvoke(args)
            try:
                result_str = json.dumps(result)
            except TypeError:
                # Fallback to a simple string if not JSON serializable
                result_str = str(result)
            return {
                "type": "conversation.item.create",
                "item": {
                    "id": tool_call["call_id"],
                    "call_id": tool_call["call_id"],
                    "type": "function_call_output",
                    "output": result_str,
                },
            }

        return asyncio.create_task(run_tool())
    

    async def output_iterator(self) -> AsyncIterator[dict]:
        """
        Yields events. Each time a tool call is added (via add_tool_call).
        """
        trigger_task = asyncio.create_task(self._trigger_func())
        tasks = {trigger_task}

        while not self._stop:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tasks.remove(task)

                # If self._stop is set inside the loop, we can break early:
                if self._stop:
                    break

                if task == trigger_task:
                    # Received a new tool call
                    async with self._lock:
                        # Reset the future for the next tool call
                        self._trigger_future = asyncio.Future()
                    trigger_task = asyncio.create_task(self._trigger_func())
                    tasks.add(trigger_task)

                    tool_call = task.result()
                    try:
                        new_task = await self._create_tool_call_task(tool_call)
                        tasks.add(new_task)
                    except ValueError as e:
                        # If there's a parsing or missing tool error, yield it immediately
                        yield {
                            "type": "conversation.item.create",
                            "item": {
                                "id": tool_call["call_id"],
                                "call_id": tool_call["call_id"],
                                "type": "function_call_output",
                                "output": (f"Error: {str(e)}"),
                            },
                        }
                else:
                    # A tool call has completed
                    yield task.result()
            if self._stop:
                break
        # Clean up tasks
        for t in tasks:
            if not t.done():
                t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print("VoiceToolExecutor: output_iterator stopped cleanly.")


@beta()
class OpenAIVoiceReactAgent(BaseModel):
    model: str = Field(default=DEFAULT_MODEL)
    api_key: SecretStr = Field(
        alias="openai_api_key",
        default_factory=secret_from_env("OPENAI_API_KEY", default=""),
    )
    instructions: str | None = None
    tools: list[BaseTool] | None = None
    url: str = Field(default=DEFAULT_URL)

    async def aconnect(
        self,
        input_stream: AsyncIterator[str],
        send_output_chunk: Callable[[str], Coroutine[Any, Any, None]],
        system_start_time: float,
        speaker: Speaker,
    ) -> None:
        """
        Connect to the OpenAI API and send/receive messages in real-time.

        input_stream: AsyncIterator[str]
            A stream of input events (often audio) to send to the model. Usually transports input_audio_buffer.append events from the microphone.
        send_output_chunk: Callable[[str], Coroutine[Any, Any, None]]
            Callback to receive output events (often audio chunks). Usually sends response.audio.delta events to the speaker.
        """
        tools_by_name = {tool.name: tool for tool in (self.tools or [])}
        tool_executor = VoiceToolExecutor(tools_by_name=tools_by_name)

        async with connect(
            model=self.model, 
            api_key=self.api_key.get_secret_value(), 
            url=self.url
        ) as (model_send, model_receive_stream):
            
            done_with_audio_output = False

            # Prepare function (tool) definitions
            tool_defs = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object", 
                        "properties": tool.args
                    },
                }
                for tool in tools_by_name.values()
            ]
            print("-----------------------------------")
            print(f"Loaded Tools: \n")
            for tool in tool_defs:
                print(f"{tool}\n")

            # Send an initial session update containing instructions & tool definitions
            await model_send(
                {
                    "type": "session.update",
                    "session": {
                        "instructions": self.instructions,
                        "output_audio_format": "pcm16",
                        "input_audio_transcription": {
                            "model": "whisper-1",
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "create_response": True,
                            "interrupt_response": False,
                        },
                        "tools": tool_defs,
                        "temperature": 0.7,
                        "voice": "alloy",
                    },
                }
            )

            startup_elapsed = time.time() - system_start_time
            with open("tests/system_start_time_measurements.txt", "a", encoding="utf-8") as f:
                f.write(f"{startup_elapsed:.3f}\n")

            # Merge three streams:
            # 1. input_mic: your live input stream (e.g., audio or text typed by the user)
            # 2. output_speaker: events returned from the model (e.g., audio or system messages)
            # 3. tool_outputs: results from calling custom tools (AddTwoNumbersTool, etc.)
            try:
                async for stream_key, data_raw in amerge(
                    input_mic=input_stream,
                    output_speaker=model_receive_stream,
                    tool_outputs=tool_executor.output_iterator(),
                ):
                    
                    if time.time() - system_start_time > 120:
                        break
                    # Convert string JSON to dict if needed
                    try:
                        data = (
                            json.loads(data_raw) if isinstance(data_raw, str) else data_raw
                        )
                    except json.JSONDecodeError:
                        print("Error decoding data:", data_raw)
                        continue

                    # Distribute events based on which stream produced them
                    if stream_key == "input_mic" and not done_with_audio_output:
                        # Forward user/mic events to the OpenAI Realtime API
                        await model_send(data)

                    elif stream_key == "tool_outputs" and not done_with_audio_output:
                        # Tool executor produced a new result
                        logger.info(f"Tool output: {data}")
                        await model_send(data)
                        await model_send({"type": "response.create", "response": {}})

                    elif stream_key == "output_speaker":
                        # Events coming back from the model
                        event_type = data["type"]

                        if event_type == "response.audio.delta":
                            # Send audio chunk to TTS or audio playback
                            await send_output_chunk(json.dumps(data))

                        elif event_type == "input_audio_buffer.speech_started":
                            print("\nNew speech detected...")
                            await send_output_chunk(json.dumps(data))

                        elif event_type == "input_audio_buffer.speech_stopped":
                            # Change LEDs
                            subprocess.run(["python", PIXEL_RING_PATH, "wait_mode"])
                            print("\nSpeech is terminated. Processing...")


                        elif event_type == "error":
                            print("error:", data)

                        elif event_type == "response.function_call_arguments.done":
                            # This is where the model signals it wants to call a tool with arguments
                            logger.info(f"Tool call requested: {data}")
                            await tool_executor.add_tool_call(data)

                        elif event_type == "response.audio_transcript.done":
                            # Completed text transcript
                            logger.info(f"Model: {data['transcript']}")
                            done_with_audio_output = True

                            while(speaker.is_playing()):
                                await asyncio.sleep(0.5)
                            subprocess.run(["python", PIXEL_RING_PATH, "turn_off"])
                            break


                        elif event_type == "conversation.item.input_audio_transcription.completed":
                            # Completed user transcription
                            logger.info(f"User: {data['transcript']}")

                        elif event_type == "response.audio.done":
                            input_stream.stop()
                            await send_output_chunk(json.dumps(data))


                        elif event_type == "response.created":
                            subprocess.run(["python", PIXEL_RING_PATH, "speak_mode"])

                        # elif event_type in EVENTS_TO_IGNORE:
                        #     pass

                        print(event_type)
            finally:
                tool_executor.stop()
