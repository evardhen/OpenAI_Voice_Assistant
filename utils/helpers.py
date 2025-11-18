import json
import base64
from .speaker import Speaker


async def output_audio_chunk(response_str: str, speaker: Speaker):
    """
    Handle audio output from a model's response.
    """
    try:
        event = json.loads(response_str)
    except json.JSONDecodeError:
        print("Could not parse audio event:", response_str)
        return

    if event.get("type") == "response.audio.delta":
        encoded_audio = event.get("delta", "")
        if encoded_audio:
            raw_data = base64.b64decode(encoded_audio)
            await speaker.play_chunk(raw_data)
