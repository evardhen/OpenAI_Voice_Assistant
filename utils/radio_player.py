from loguru import logger
import sys
import ffmpeg
import sounddevice as sd
import soundfile as sf
import multiprocessing
import queue

import numpy as np

# Configure loguru
logger.remove()  # Remove any existing handlers
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")

# you can find example web radfio stations here: https://hendrikjansen.nl/henk/streaming3.html
class AudioPlayer:

	def __init__(self, volume = 0.5):
		self._process = None
		self._volume = volume
		self._counter = 0
		self._current_source = None
		
	def play_file(self, file):
		if self._process:
			self.stop()
			
		self._process = multiprocessing.Process(target=self._play_file, args=(file,))
		self._process.start()
		
	def play_stream(self, source):
		self._current_source = source
		if self._process:
			self.stop()
		self._process = multiprocessing.Process(target=self._play_stream, args=(source, ))
		self._process.start()
		
	def _play_file(self, file):
		sd.default.reset()
		data, fs = sf.read(file, dtype='float32')
		sd.play(data * self._volume, fs, device=sd.default.device['output'])
		status = sd.wait()
		if status:
			logger.error("Error with playing sound: {}.", status)
			
	def _play_stream(self, source):
		sd.default.reset()
		_q = queue.Queue(maxsize=20)

		logger.debug(f"Playing on device number: {sd.default.device['output']}.")
		
		def _callback_stream(outdata, frames, time, status):
			if status.output_underflow:
				raise sd.CallbackAbort
			assert not status
			
			try:
				data = _q.get_nowait()
				data = data * self._volume
			except queue.Empty as e:
				raise sd.CallbackAbort from e
			assert len(data) == len(outdata)
			outdata[:] = data
			
		try:
			info = ffmpeg.probe(source)
		except Exception as e:
			logger.error(e)
			
		streams = info.get('streams', [])
		if len(streams) != 1:
			logger.error('Only one stream can be inputted.')
		
		stream = streams[0]
		
		if stream.get('codec_type') != 'audio':
			logger.error("Stream has to be an audio stream.")
			
		channels = stream['channels']
		samplerate = float(stream['sample_rate'])
		
		try:
			process = ffmpeg.input(source).output('pipe:', format='f32le', acodec='pcm_f32le', ac=channels, ar=samplerate, loglevel='quiet').run_async(pipe_stdout=True)
			#process = ffmpeg.input(source).filter('volume', self._volume).output('pipe:', format='f32le', acodec='pcm_f32le', ac=channels, ar=samplerate, loglevel='quiet').run_async(pipe_stdout=True)
			#stream = sd.RawOutputStream(samplerate=samplerate, blocksize=1024, device=sd.default.device['output'], channels=channels, dtype='float32', callback=_callback_stream)
			stream = sd.OutputStream(samplerate=samplerate, blocksize=1024, device=sd.default.device['output'], channels=channels, dtype='float32', callback=_callback_stream)
			read_size = 1024 * channels * stream.samplesize
			for _ in range(20):
				data = np.frombuffer(process.stdout.read(read_size), dtype='float32')
				data.shape = -1, channels
				_q.put_nowait(data)
			logger.debug("Starting radio stream...")
			with stream:
				timeout = 1024 * 20 / samplerate
				try:
					while True:
						data = np.frombuffer(process.stdout.read(read_size), dtype='float32')
						data.shape = -1, channels					
						_q.put(data, timeout=timeout)
				except KeyboardInterrupt:
					logger.debug("Stopping radio stream...")
		except queue.Full as e:
			if self._counter < 3:
				logger.error(f"Streaming-Queue is full, retry playing: Attempt {self._counter + 1}")
				self._play_stream(source)
			else:
				logger.error("Streaming-Queue is full, could not start radio player.")
		except Exception as e:
			logger.error(e)

	def stop(self):
		if self._process:
			self._process.terminate()

	def is_playing(self):
		return self._process and self._process.is_alive()

	def set_volume(self, volume):
		self._volume = max(0.0, min(volume, 1.0))
		if volume > 1.0:
			logger.debug("The volume of the audioplayer is set to the maximum value of 1.0, not {}.", volume)

	def get_volume(self):
		return self._volume


if __name__ == "__main__":
    #player = AudioPlayer("http://mp3channels.webradio.rockantenne.de/classic-perlen")
    player = AudioPlayer()
    player.set_volume(0.5)
    #player.play_file("Do I Wanna Know.wav")
    #player.play_stream("http://mp3channels.webradio.rockantenne.de/classic-perlen")
    player.play_stream("http://fritz.de/livemp3")
