import unittest
import time
import os, sys
parent = os.path.abspath('.')
sys.path.insert(1, parent)
from utils.radio_player import AudioPlayer


class AudioPlayerTest(unittest.TestCase):

    def test_play_audio(self):
        player = AudioPlayer("http://fritz.de/livemp3")
        assert(not player.is_playing())
        player.play()
        # Assert that the player is playing audio
        assert(player.is_playing())
        time.sleep(4)
        # Stop playing audio and assert that the player is no longer playing
        player.stop()
        assert(not player.is_playing())


if __name__ == '__main__':
    unittest.main()