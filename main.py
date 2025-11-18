import asyncio
import time
import pyaudio
import dotenv
import argparse
from loguru import logger
import os
import pvporcupine
import subprocess
from flask import Flask, request, jsonify
import threading
import struct
import sys

from intents import TOOLS
from utils.realtime_api import OpenAIVoiceReactAgent
from utils import open_microphone, KEYWORD_PATH, MODEL_FILE_PATH, PIXEL_RING_PATH, Speaker, output_audio_chunk, SYSTEM_PROMPT
import utils.global_variables as global_variables
from utils.spotify_management import Spotify
from utils.radio_player import AudioPlayer

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

class VoiceAssistant():

    def __init__(self):
        self.audio_frames = []
        self.default_wakeword = 'Hey Luna'

        dotenv.load_dotenv()
        self.select_microphone()
        self.initialize_spotify()
        self.initialize_wakeword_detection()
        self.initialize_music_stream()
        self.initialize_pixel_ring()
        self.initialize_touch_sensor_server()
        self.initialize_agent()
        self.initialize_speaker()
        logger.debug("Initialization completed.")

    def select_microphone(self):
        self.pyAudio = pyaudio.PyAudio()
        parser = argparse.ArgumentParser(description='Select microphone.')
        parser.add_argument('-m', '--microphone', type=int, help='Index of the microphone to use')
        args = parser.parse_args()

        if args.microphone is not None:
            self.microphone_index = args.microphone
        else:
            self.microphone_index = None

            # Print available microphones
            print("\nList of available microphones:\n")
            for i in range(self.pyAudio.get_device_count()):
                device_info = self.pyAudio.get_device_info_by_index(i)
                print(f"Device {i}: {device_info['name']} (Sample Rate: {device_info['defaultSampleRate']} Hz, Channels: {device_info['maxInputChannels']})")

            # Ask user to select a microphone
            while self.microphone_index is None:
                try:
                    self.microphone_index = int(input("\nEnter the index of the microphone you want to use: "))
                    if not (0 <= self.microphone_index < self.pyAudio.get_device_count()):
                        print(f"Invalid microphone index. Please select an index between 0 and {self.pyAudio.get_device_count()}.")
                        self.microphone_index = None
                except ValueError:
                    print("Invalid input format. Please enter a valid microphone index as an integer.")

    def initialize_spotify(self):
        global_variables.spotify = Spotify()


    def initialize_wakeword_detection(self):
        logger.debug("Starting wake word detection....")
        self.wakewords = [self.default_wakeword]
        logger.debug('Wake words are: {}', ', '.join( self.wakewords))

        PICOVOICE_KEY = os.environ.get('PICOVOICE_KEY')
        self.porc = pvporcupine.create(access_key=PICOVOICE_KEY, keyword_paths=[KEYWORD_PATH], model_path=MODEL_FILE_PATH)
        self.audio_stream = self.pyAudio.open(rate = self.porc.sample_rate, channels=1, format = pyaudio.paInt16, input=True, frames_per_buffer=self.porc.frame_length, input_device_index= self.microphone_index)
    
    def initialize_music_stream(self):
        global_variables.radio_player = AudioPlayer(volume=1.0)

    def initialize_pixel_ring(self):
        # Start the subprocess
        command = ["python", PIXEL_RING_PATH, "initialize_pixel_ring"]
        subprocess.run(command)

    def initialize_speaker(self):
        self.speaker = Speaker()

    def initialize_agent(self):
        self.agent = OpenAIVoiceReactAgent(
        instructions=SYSTEM_PROMPT,
        tools=TOOLS
        )

    def initialize_touch_sensor_server(self):
        self.touch_server = Flask(__name__)
        self.lock = threading.Lock()  # Thread safety
        self.last_touch_time = 0      # Track the last time a touch event was processed
        self.cooldown_period = 1      # Cooldown period in seconds

        @self.touch_server.route('/api/touch', methods=['POST'])
        def handle_touch():
            try:
                data = request.get_json()
                if 'message' in data:
                    current_time = time.time()
                    # Thread-safe update of the flag
                    with self.lock:
                        if current_time - self.last_touch_time < self.cooldown_period or self.start_speech_recognition == True:
                            return jsonify({"status": "error", "message": "Cooldown active, try again later"}), 429
                    
                        self.last_touch_time = current_time
                        self.start_speech_recognition = True
                    return jsonify({"status": "success", "message": "Touch event received!"}), 200
                else:
                    return jsonify({"status": "error", "message": "Invalid data"}), 400
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

    async def recognize_speech(self, mic_stream):
        start_time = time.time()  # Start time for overall process        
        # Activate LEDs
        subprocess.run(["python", PIXEL_RING_PATH, "activate_doa"])

        # Mute other devices while listening
        if global_variables.radio_player.is_playing():
            logger.debug(f"Stopped the radio player.")
            global_variables.radio_player.stop()
        if global_variables.spotify.is_spotify_playing():
            logger.debug(f"Set spotify volume to mute volume: {0.0}")
            global_variables.spotify.stop()
        
        await self.agent.aconnect(
            input_stream=mic_stream, 
            send_output_chunk=lambda chunk: output_audio_chunk(chunk, self.speaker),
            system_start_time=start_time,
            speaker=self.speaker,
        )

        end_time = time.time()
        overall_duration = end_time - start_time

        # Logging times to a file
        with open("./logs/durations_log.txt", "a") as file:
            file.write(f"overall: {overall_duration:.2f}\n")

    def run_touch_sensor(self):
        logger.info("Restarting touch sensor server...")
        self.touch_server.run(host='0.0.0.0', port=5000)

    async def run(self):
        logger.info("VoiceAssistant started...")

        try:
            self.start_speech_recognition = False
            # Create a thread for the touch sensor
            touch_sensor_thread = threading.Thread(target=self.run_touch_sensor)
            touch_sensor_thread.daemon = True
            touch_sensor_thread.start()

            while True:
                pcm = self.audio_stream.read(self.porc.frame_length)
                pcm_unpacked =  struct.unpack_from("h" * self.porc.frame_length, pcm)
                keyword_index = self.porc.process(pcm_unpacked)
                with self.lock:
                    trigger_speech = self.start_speech_recognition
                if keyword_index >= 0 or trigger_speech: # -1, if no keyword was detected
                    if keyword_index >= 0:
                        logger.info("Wakeword '{}' detected. How can I help you?", self.wakewords[keyword_index])
                    else:
                        logger.info("Voice assistant triggered by touch event.")

                    async with open_microphone() as mic_stream:
                        subprocess.run(["python", PIXEL_RING_PATH, "activate_doa"])
                        logger.info("Websocket starting...")
                        await self.recognize_speech(mic_stream)
                        logger.info("Websocket terminated...")

                    # Reset variables
                    keyword_index = -1
                    with self.lock:
                        self.start_speech_recognition = False
            
        except KeyboardInterrupt:
            print("\n")
            logger.info("Process interrupted by keyboard.")
            raise
        finally:
            logger.debug('Closing open packages...')
            if self.porc:
                self.porc.delete()
            if self.audio_stream is not None:
                self.audio_stream.close()
            if global_variables.radio_player is not None:
                global_variables.radio_player.stop()
            self.speaker.close()

            # Turn off LEDs
            subprocess.run(["python", PIXEL_RING_PATH, "turn_off"])


def run_voice_assistant():
    
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        assistant = VoiceAssistant()
        try:
            loop.run_until_complete(assistant.run())
        except KeyboardInterrupt:
            print("Caught Ctrl+C. Shutting down gracefully...")
            # Cancel all running tasks so they can handle cleanup
            tasks = asyncio.all_tasks(loop)
            for t in tasks:
                t.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            break
        except Exception as e:
            logger.exception(f"Unhandled exception: {e}. Restarting VoiceAssistant...")
            time.sleep(1)  # Delay before restarting to prevent immediate and continuous restarts
        finally:
            loop.close()

if __name__ == "__main__":
    run_voice_assistant()