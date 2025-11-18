from langdetect import detect
from gtts import gTTS
from pydub import AudioSegment
from pydub.effects import speedup
import numpy as np
import sounddevice as sd
import soundfile as sf

SPEECH_FILE_PATH = "output.mp3"

def detect_language(string, default_language):
    detected_language = detect(string)
    if detected_language not in ["de", "en"]:
        detected_language = default_language
    return detected_language

def change_volume(audio, volume_change_percent):
    # Convert volume change from percent to dB
    if volume_change_percent == 0:
        return audio
    elif volume_change_percent > 0:
        volume_change_db = 20 * np.log10(1 + volume_change_percent / 100)
    else:
        volume_change_db = -20 * np.log10(1 - volume_change_percent / 100)
    # Apply volume change
    return audio + volume_change_db

def speak_gtts(text, volume_change_percent, speed, default_language):
    detected_language = detect_language(text, default_language)

    tts = gTTS(text=text, lang=detected_language, slow=False)
    # Saving the converted audio in a BytesIO object
    tts.save(SPEECH_FILE_PATH)

    audio = AudioSegment.from_mp3(SPEECH_FILE_PATH)
    audio = change_volume(audio, volume_change_percent)

    chunk_size = 150 # in milliseconds
    if speed != 1.0:
        audio = speedup(audio, speed, chunk_size)
    audio.export("output_modified.wav", format="wav")

    # Read the wav file
    data, fs = sf.read("output_modified.wav")
    # Play the audio
    sd.play(data, fs)
    sd.wait()

    print("Finished...")

if __name__ == "__main__":
    text = "Hallo, wie kann ich dir helfen?"
    speak_gtts(text, 0, 1.0, "de")
