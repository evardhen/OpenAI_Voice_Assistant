from loguru import logger

def interrupt(va):
    if va.tts.is_busy():
        va.tts.stop()
        logger.debug("Voice Assistant wurde gestoppt.")
    if va.audioplayer.is_playing():
        va.audioplayer.stop()
        logger.debug("Audiostream wurde gestoppt.")
    if va.spotify.is_playing:
        va.spotify.stop()
    return ""