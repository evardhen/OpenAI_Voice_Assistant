from langchain import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import StructuredTool
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import dotenv
import time

dotenv.load_dotenv()
CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')
SCOPE="user-read-playback-state,user-modify-playback-state,user-read-private,user-read-email,playlist-read-private,playlist-read-collaborative,user-library-read"

# os.environ["LANGCHAIN_TRACING"] = "true"

def spotify_playback(song_title: Optional[str] = None, artist_name: Optional[str] = None, album_name: Optional[str] = None, playlist_name: Optional[str] = None) -> str:
    """
    Lets you specify a song, artist, album, or playlist to play on Spotify. The inputs are optional and each input variable is a separate string without json formatting.
    """
    try:
        spotify_player = CustomSpotifyPlayer()
    except Exception as e:
        return f"Error: {e}"
    if song_title and artist_name and song_title != "null" and artist_name != "null":
        song_info = spotify_player.play_song_from_artist(song_title, artist_name)
        return f"Playing {song_info['name']} by {song_info['artists'][0]['name']} 1 \n"
    if song_title and song_title != "null":
        song_info = spotify_player.play_song(song_title)
        return f"Playing {song_info['name']} by {song_info['artists'][0]['name']} 2 \n"
    if artist_name and artist_name != "null":
        song_info = spotify_player.play_artist(artist_name)
        return "Playing songs by " + artist_name + "3\n"
    if album_name and album_name != "null":
        song_info = spotify_player.play_album(album_name)
        return "Playing the album " + album_name + "4\n"
    if playlist_name and playlist_name != "null":
        song_info = spotify_player.play_playlist(playlist_name)
        return "Playing songs from the playlist " + playlist_name + "5\n"


class CustomSpotifyPlayer:
    def __init__(self):
        SPOTIFY_AUTH=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)
        ACCESS_TOKEN = SPOTIFY_AUTH.get_access_token(as_dict=False)
        self.sp = spotipy.Spotify(ACCESS_TOKEN)
        # Get the user's available devices
        try:
            self.devices = self.sp.devices()
        except Exception as e:
            if str(e).find("The access token expired") != -1:
                raise Exception("Your Spotify access token has expired.")
            elif str(e).find("Invalid access token") != -1:
                raise Exception("Invalid spotify access token.")
            raise Exception("Can't get devices list: " + str(e))

        # assuming the first device is the one we want
        try:
            self.device_id = self.devices["devices"][0]["id"]
            if not self.device_id:
                raise Exception("No device found, please make sure you have one connected")
        except Exception as e:
            raise Exception("Can't get device id: " + str(e))
        


    def play_song_from_artist(self, song_name, artist_name):
        # Search for the song
        results = self.sp.search(
            q=f"track:{song_name} artist:{artist_name}", limit=1, type="track"
        )

        # Get the first song from the search results
        song_uri = results["tracks"]["items"][0]["uri"]

        # Start playback
        self.sp.start_playback(device_id=self.device_id, uris=[song_uri])
        return results["tracks"]["items"][0]

    def play_song(self, song_name):
        # Search for the song
        results = self.sp.search(q=song_name, limit=1, type="track")

        # Get the first song from the search results
        song_uri = results["tracks"]["items"][0]["uri"]

        # Start playback
        self.sp.start_playback(device_id=self.device_id, uris=[song_uri])
        return results["tracks"]["items"][0]

    def play_artist(self, artist_name):
        # Search for the artist
        results = self.sp.search(q=artist_name, limit=1, type="artist")

        # Get the first artist from the search results
        artist_uri = results["artists"]["items"][0]["uri"]

        # Start playback
        self.sp.start_playback(device_id=self.device_id, context_uri=artist_uri)
        return results["artists"]["items"][0]

    def play_album_from_artist(self, album_name, artist_name):
        # Search for the album
        results = self.sp.search(
            q=f"{album_name} artist:{artist_name}", limit=1, type="album"
        )

        # Get the first album from the search results
        album_uri = results["albums"]["items"][0]["uri"]

        # Start playback
        self.sp.start_playback(device_id=self.device_id, context_uri=album_uri)
        return results["albums"]["items"][0]

    def play_album(self, album_name):
        # Search for the album
        results = self.sp.search(q=album_name, limit=1, type="album")

        # Get the first album from the search results
        album_uri = results["albums"]["items"][0]["uri"]

        # Start playback
        self.sp.start_playback(device_id=self.device_id, context_uri=album_uri)
        return results["albums"]["items"][0]

    def play_playlist(self, playlist_name):
        # Search for the playlist
        results = self.sp.search(q=playlist_name, limit=1, type="playlist")

        # Get the first playlist from the search results
        playlist_uri = results["playlists"]["items"][0]["uri"]

        # Start playback
        self.sp.start_playback(device_id=self.device_id, context_uri=playlist_uri)
        return results["playlists"]["items"][0]
    

if __name__ == "__main__":
    llm = OpenAI(temperature=0)
        
    tool = StructuredTool.from_function(spotify_playback)
    # Structured tools are compatible with the STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION agent type.
    agent_executor = initialize_agent(
        [tool],
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )
    agent_executor.run("Play Perfect from Ed Sheeran on Spotify.")
    time.sleep(10)
    agent_executor.run("Can you play that song again?")

