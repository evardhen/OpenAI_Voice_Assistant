from usb_4_mic_array.tuning import Tuning
import usb.core
import usb.util
import time
from loguru import logger

def speech_activity_detection(threshhold):
    counter = 0
    dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    if dev:
        Mic_tuning = Tuning(dev)
        while True:
            if Mic_tuning.is_voice() == 0:
                counter += 1
            if counter > threshhold:
                logger.debug("Thread 2 zur Spracherkennung erfolgreich beendet.")
                break
            time.sleep(0.5)