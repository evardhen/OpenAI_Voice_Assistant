# Voice Assistant Luna

## Overview

Meet Luna, the versatile voice assistant designed specifically for the unique environment of Zeki's kitchen. Luna stands out with its wide range of functionalities, from standard voice assistant capabilities to exclusive, kitchen-specific features.

## Language Flexibility

Luna is linguistically adept, ready to assist in any language supported by the active OpenAI model.

## Usage Guide

1.	Activation: Luna is on standby when the voice assistant lights are off. It eagerly awaits your command, activated by the wake word.
   - Touch: Tap on the VA for atleast 1 second (ESP32 triggers activation via WIFI)
   - Wake Word: Initiate interaction by saying, "Hey Luna" This simple phrase brings Luna to life. Don’t forget the „Hey“ in „Hey Luna“.
4.	Visual Feedback:
  - Voice Detection: Upon hearing the wake word, Luna's LEDs illuminate, indicating the direction from which your voice is detected (DOA).
  - Processing Mode: Once Luna has captured your command, the LEDs switch to a distinctive pattern, signaling that your request is being processed.
  - Response Mode: As Luna prepares to respond, the LEDs adapt to a unique pattern, signifying the answer is on its way.
4.	Ready for More: After responding, Luna's LEDs switch off, indicating it's ready for your next command.

## Terminal Control

In the wakeword_detection() function in the main file, you have to select the correct microphone (1 normally). You can identify it by commenting in the block and run the main. Afterwards, you have to adapt the microphone in the init of class VoiceAssistant().  

Run the script: python main.py -m 1

## Supported Features

Currently, there are 13 intents implemented:
- Open/Close kitchen cupboards
- Google search
- Change Volume
- Change Voice Speed
- Get Time
- Grocery Detection
- Get Date
- Get Temperature
- Spotify player
- Radio Player
- Stop Music
- Read inventory
