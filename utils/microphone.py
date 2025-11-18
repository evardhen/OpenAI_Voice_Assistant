import asyncio
import json
import base64
import pyaudio
import queue
import threading
from typing import AsyncIterator
from contextlib import asynccontextmanager
from loguru import logger

from .constants import CHUNK_SIZE, FORMAT, CHANNELS, RATE

class MicGenerator:
    def __init__(self, audio_queue: queue.Queue, stop_event: threading.Event):
        self.audio_queue = audio_queue
        self.stop_event = stop_event

    def stop(self):
        """Stop sending audio immediately."""
        logger.info("Stopped audio input stream")
        self.stop_event.set()

    def __aiter__(self):
        # Return the async iterator (self)
        return self

    async def __anext__(self) -> str:
        # Wait for the next chunk from the queue (executed in a worker thread)
        chunk = await asyncio.to_thread(self.audio_queue.get)
        
        if self.stop_event.is_set():
            raise StopAsyncIteration
        
        return chunk


@asynccontextmanager
async def open_microphone() -> AsyncIterator[MicGenerator]:
    """
    Async context manager that yields an async generator of audio events.
    Internally, microphone capture runs on a separate thread.
    """
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    def mic_thread():
        """
        Thread target: Continuously read audio from PyAudio and push into the queue.
        """
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE
        )
        try:
            while not stop_event.is_set():
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                encoded = base64.b64encode(data).decode("utf-8")
                event_json = json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": encoded
                })
                audio_queue.put(event_json)
        except Exception as e:
            print("Microphone thread exception:", e)
        finally:
            # Push a final 'end' event so the async generator can finish gracefully
            # audio_queue.put(json.dumps({"type": "input_audio_buffer.clear"}))
            stream.stop_stream()
            stream.close()
            p.terminate()

    # Start the microphone capture thread
    t = threading.Thread(target=mic_thread, daemon=True)
    t.start()
    print("Microphone activated in separate thread...")


    mic_gen = MicGenerator(audio_queue, stop_event)
    try:
        yield mic_gen
    finally:
        stop_event.set()
        t.join()
