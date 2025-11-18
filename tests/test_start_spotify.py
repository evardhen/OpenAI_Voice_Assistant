import unittest
import os, sys

dir = os.path.join(os.path.dirname(__file__), '../intents/functions/start_spotify/')
sys.path.insert(0, dir)
dir = os.path.join(os.path.dirname(__file__), '../')
sys.path.insert(0, dir)
from utils.spotify_management import Spotify
#import intent_start_spotify


class StartSpotifyTest(unittest.TestCase):

    def test_play_spotify(self):
        sp = Spotify(0.3)
        sp.play_spotify("Perfekt", "track")
if __name__ == '__main__':
    unittest.main()
