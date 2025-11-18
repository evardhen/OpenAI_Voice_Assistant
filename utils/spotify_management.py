import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import dotenv
from loguru import logger
import yaml
import time

class Spotify():
    def __init__(self):
        """
        To enter the credentials of your spotify account, set them as environmental variables on your machine or add them to the '.env' file (listed in .gitignore) beforehand and execute this code:
        Method 1:
        On Windows:
        setx SPOTIFY_USERNAME your_username_here
        setx SPOTIFY_PASSWORD your_password_here
        setx SPOTIFY_URI your_uri_here
        On Linux and Mac:
        export SPOTIFY_USERNAME=your_username_here
        export SPOTIFY_PASSWORD=your_password_here
        export SPOTIFY_URI=your_uri_here

        Method 2:
        Load environment variables from .env file
        """
        self._is_playing = False
        self.is_playing_time_limit = 180 # In seconds, timer for how often the variables is_playing is updated
        self.is_playing_current_time = time.time()
        dotenv.load_dotenv()

        # Get the spotify credentials from environment variables
        client_id = os.environ.get('SPOTIPY_CLIENT_ID')
        client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
        redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')
        scope="user-read-playback-state,user-modify-playback-state,user-read-private,user-read-email,playlist-read-private,playlist-read-collaborative,user-library-read"

        # Initialize Spotipy with your credentials
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope))
        
        # Find the ID of the first recognized device to play spotify on
        self.device_id = None
        computer_name = "KITCHEN_VA"  # Replace with your computer's Spotify name
        devices = self.sp.devices()
        for device in devices['devices']:
            logger.debug("Device name for Spotify: {}", device['name'])
            if device['name'] == computer_name:
                self.device_id = device['id']
                logger.info("Using Spotify on device: {}", device['name'])
                break
        if not self.device_id:
            logger.error("No Spotify application detected.")


    def stop(self):
        self.sp.pause_playback(device_id=self.device_id)
        self._is_playing = False

    def _volume_abs_to_percent(self, volume):
        if volume > 2:
            logger.debug("Volume {} is limited to a maximum of 2.", volume)
            volume = 2
        return int(volume * 100)

    def get_volume(self):
        return self.volume / 100.

    def set_volume(self, volume):
        self.volume_percent = self._volume_abs_to_percent(volume)
        self.sp.volume(volume_percent=self.volume_percent, device_id=self.device_id)
        logger.debug("Spotify volume changed to {} percent.", self.volume_percent)

    def is_spotify_playing(self):
        self._update_is_playing()
        return self._is_playing
    
    def _update_is_playing(self):
        if time.time() - self.is_playing_current_time < self.is_playing_time_limit or self._is_playing == False:
            return
        
        self.is_playing_current_time = time.time()
        print("Updating is_playing...")
        current_playback = self.sp.current_playback()
        if current_playback is not None and current_playback['is_playing']:
            self._is_playing = True
        else:
            self._is_playing = False


if __name__ == '__main__':
    sp = Spotify(0.3)
