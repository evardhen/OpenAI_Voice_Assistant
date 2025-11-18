import yaml
import text2numde
from fuzzywuzzy import fuzz
import os
import re
from loguru import logger
import random


def start_radio(audioplayer, volume, language, name):
    config_path = os.path.join("./intents/config_start_radio.yaml")
    with open(config_path, "r", encoding="utf-8") as file:
        config_file = yaml.load(file, Loader=yaml.FullLoader)

    # if no slot has been detected, play a random radio stream (see start_radio_dataset.yaml)
    if name == None or name == "":
        return random.choice(config_file['intent']['start_radio']['radio_station'])

    # convert text numbers to real numbers
    radio_station = text2numde.sentence2num(name)
    # eliminate unnecessary spaces
    radio_station = re.sub(' +', ' ', radio_station)

    for name, URL in config_file['intent']['start_radio']['radio_station'].items():
        ratio = fuzz.ratio(radio_station.lower(), name.lower())
        logger.info("Übereinstimmung von {} und {} ist {}%", radio_station, name, ratio)
        if ratio > 70:
            audioplayer.set_volume(volume)
            audioplayer.play_stream(URL)
            return ""

    for name, path in config_file['intent']['start_radio']['file_name'].items():
        ratio = fuzz.ratio(radio_station.lower(), name.lower())
        logger.info("Übereinstimmung von {} und {} ist {}%", radio_station, name, ratio)
        if ratio > 70:
            audioplayer.set_volume(volume)
            audioplayer.play_file(path)
            #player.play_file("Do I Wanna Know.wav")
            return ""

    return random.choice(config_file['intent']['start_radio'][language]['unknown_name'])