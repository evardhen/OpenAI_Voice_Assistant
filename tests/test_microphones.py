import pyaudio
import wave
import numpy as np

microphone_index = 1

def print_available_microphones():
    audio = pyaudio.PyAudio()
    print("Available microphones:")
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {device_info['name']} (Sample Rate: {device_info['defaultSampleRate']} Hz, Channels: {device_info['maxInputChannels']})")
    audio.terminate()

def record_audio(file_name, duration=6, sample_rate=44100, channels=2, chunk=1024):
    audio = pyaudio.PyAudio()

    # Set up the audio stream
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        input_device_index=microphone_index,
                        frames_per_buffer=chunk)

    print("Recording...")

    frames = []
    for i in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Finished recording.")

    # Stop and close the audio stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio to a WAV file
    wave_file = wave.open(file_name, 'wb')
    wave_file.setnchannels(channels)
    wave_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    wave_file.setframerate(sample_rate)
    wave_file.writeframes(b''.join(frames))
    wave_file.close()

if __name__ == "__main__":
    file_name = "recorded_audio.wav"
    # print_available_microphones()
    record_audio(file_name, sample_rate=16000, channels=1)
