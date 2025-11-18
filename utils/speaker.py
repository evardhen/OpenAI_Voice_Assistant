import pyaudio
from .constants import FORMAT, CHANNELS, RATE

import multiprocessing
import pyaudio

def audio_player_worker(queue):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
    while True:
        audio_chunk = queue.get()
        if audio_chunk is None:  # None signals shutdown.
            break
        stream.write(audio_chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()

class Speaker:
    """
    Class for playing back audio chunks in a dedicated process.
    """
    def __init__(self):
        self.queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=audio_player_worker, args=(self.queue,))
        self.process.start()

    async def play_chunk(self, audio_chunk: bytes):
        # Simply put the audio chunk into the queue.
        self.queue.put(audio_chunk)

    def is_playing(self):
        # This approach may require additional signaling to know if playback is in progress.
        # Here, we just check if the queue has pending items.
        return not self.queue.empty()

    def close(self):
        self.queue.put(None)
        self.process.join()
