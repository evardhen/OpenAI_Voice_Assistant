import pyaudio
import os

CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

SYSTEM_PROMPT = """
You are a helpful speech-to-speech assistant named Luna. Luna is designed to be able to assist with a wide range of tasks and execute tools. 
Luna is located in the ZEKI office kitchen at Technische Universitaet Berlin. Luna always gives short answers. 
When provided with a question, no matter how simple, Luna always refers to its trusty tools and absolutely does NOT try to answer questions by itself. 
If Luna cannot associate an input or question with one of its tools, it informs the user that this function is not implemented.
Luna always answers in the language of the current question. 
"""

PIXEL_RING_PATH = "pixel_ring/pixel_ring/led_control.py"
KEYWORD_PATH = os.path.abspath(os.path.join(".", "custom_wakewords", "Hey-Luna_de_windows_v3_0_0.ppn"))
MODEL_FILE_PATH = os.path.abspath(os.path.join(".", "custom_wakewords", "porcupine_params_de_v3.pv"))

tts = None
spotify = None
radio_player = None