from fuzzywuzzy import fuzz
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import dotenv
from typing import Optional
from fuzzywuzzy import fuzz
from pydantic import Field, BaseModel
from langchain_core.tools import tool

import utils.global_variables as global_variables 


dotenv.load_dotenv()
CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI')
SCOPE="user-read-playback-state,user-modify-playback-state,user-read-private,user-read-email,playlist-read-private,playlist-read-collaborative,user-library-read"

class SpotifyToolArgs(BaseModel):
    song: Optional[str] = Field(
        default="", 
        description=("Name of the song. If no name is given, pass an empty string.")
    )
    artist: Optional[str] = Field(
        default="", 
        description=("Song, playlist or album artist. If no artist is given, pass an empty string.")
    )
    album: Optional[str] = Field(
        default="", 
        description=("Name of the album. If no album is given, pass an empty string.")
    )
    playlist: Optional[str] = Field(
        default="", 
        description=("Name of the playlist. If no playlist is given, pass an empty string.")
    )

@tool("spotify_playback", args_schema=SpotifyToolArgs)
def spotify_playback_tool(song = "", artist = "", album = "", playlist= ""):
    """"Lets you play a song, artist, album, or playlist to play on Spotify. If no album, playlist, artist or song is given, pass an empty string for that input parameter."""
    return spotify_player(song, artist, album, playlist)


def spotify_player(song_title, artist_name, album_name, playlist_name) -> str:
    """
    Lets you specify a song, artist, album, or playlist to play on Spotify.
    """
    if global_variables.radio_player.is_playing():
        global_variables.radio_player.stop()
        
    try:
        spotify_player = SpotifyPlayer()

        if song_title and artist_name and song_title != "" and artist_name != "":
            song_info = spotify_player.play_song_from_artist(song_title, artist_name)
            global_variables.spotify._is_playing = True
            return f"Playing {song_info['name']} by {song_info['artists'][0]['name']} 1 \n"
        if album_name and artist_name and album_name != "" and artist_name != "":
            song_info = spotify_player.play_album_from_artist(album_name, artist_name)
            global_variables.spotify._is_playing = True
            return "Playing the album " + album_name + "5\n"
        if song_title and song_title != "":
            song_info = spotify_player.play_song(song_title)
            global_variables.spotify._is_playing = True
            return f"Playing {song_info['name']} by {song_info['artists'][0]['name']} 2 \n"
        if artist_name and artist_name != "":
            song_info = spotify_player.play_artist(artist_name)
            global_variables.spotify._is_playing = True
            return "Playing songs by " + artist_name + "3\n"
        if album_name and album_name != "":
            song_info = spotify_player.play_album(album_name)
            global_variables.spotify._is_playing = True
            return "Playing the album " + album_name + "4\n"
        if playlist_name and playlist_name != "":
            song_info = spotify_player.play_playlist(playlist_name)
            global_variables.spotify._is_playing = True
            return "Playing songs from the playlist " + playlist_name + "5\n"
        if playlist_name == "" and album_name == "" and song_title == "" and artist_name == "":
            song_info = spotify_player.play_hits_playlist("Feel Good Morning Mix")
            global_variables.spotify._is_playing = True
            return "Playing songs from the playlist " + playlist_name + "6\n"
    except Exception as e:
        return f"Error in spotify_intent: {e}"

class SpotifyPlayer:
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
            computer_name = "KITCHEN_VA"  # Replace with your computer's Spotify name
            devices = self.sp.devices()
            for device in devices['devices']:
                if device['name'] == computer_name:
                    self.device_id = device['id']
                    break

            if not self.device_id:
                raise Exception("Device Kitchen_VA not found, please make sure you have one connected.")
        except Exception as e:
            raise Exception("Can't get device id: " + str(e))
        
        global_variables.spotify.set_volume(1.0)
        


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
        self.sp.shuffle(state=True, device_id=self.device_id)

        # Start playback
        self.sp.start_playback(device_id=self.device_id, context_uri=artist_uri)
        return results["artists"]["items"][0]


    def play_album_from_artist(self, album_name, artist_name):
        # Search for the album
        results = self.sp.search(
            q=f"album:{album_name} artist:{artist_name}", limit=10, type="album"
        )

        best_match = None
        highest_score = 0

        # Loop through results to find the best match using fuzzy matching
        for item in results["albums"]["items"]:
            current_score = fuzz.ratio(item["name"].lower(), album_name.lower())
            if current_score > highest_score:
                for artist in item['artists']:
                    artist_score = fuzz.ratio(artist['name'].lower(), artist_name.lower())
                    if artist_score > 70:  # You can adjust this threshold
                        highest_score = current_score
                        best_match = item

        if best_match:
            album_uri = best_match["uri"]

            self.sp.shuffle(state=False, device_id=self.device_id)
            # Start playback
            self.sp.start_playback(device_id=self.device_id, context_uri=album_uri)
            return best_match

        return "Could not find a similar album on spotify"


    def play_album(self, album_name):
        # Search for the album
        results = self.sp.search(q=album_name, limit=1, type="album")

        # Get the first album from the search results
        album_uri = results["albums"]["items"][0]["uri"]
        self.sp.shuffle(state=False, device_id=self.device_id)
        # Start playback
        self.sp.start_playback(device_id=self.device_id, context_uri=album_uri)
        return results["albums"]["items"][0]

    def play_playlist(self, playlist_name):
        # Search for the playlist in current users playlists first
        playlists = self.sp.current_user_playlists()
        for playlist in playlists['items']:
            ratio = fuzz.ratio(playlist['name'].lower(), playlist_name.lower())
            if ratio > 70:
                self.sp.start_playback(device_id=self.device_id, context_uri=playlist["uri"])
                return (playlist['name'])
            
        # Search for all playlists
        results = self.sp.search(q=playlist_name, limit=1, type="playlist")
        playlist_uri = results["playlists"]["items"][0]["uri"]
        self.sp.shuffle(state=True, device_id=self.device_id)
        self.sp.start_playback(device_id=self.device_id, context_uri=playlist_uri)
        return results["playlists"]["items"][0]

    def play_hits_playlist(self, playlist_name):            
        # Search for all playlists
        results = self.sp.search(q=playlist_name, limit=1, type="playlist")
        playlist_uri = results["playlists"]["items"][0]["uri"]
        self.sp.shuffle(state=True, device_id=self.device_id)
        self.sp.start_playback(device_id=self.device_id, context_uri=playlist_uri)
        return results["playlists"]["items"][0]

    def play_hits_playlist(self, playlist_name):
        # Search for all playlists
        results = self.sp.search(q=playlist_name, limit=1, type="playlist")
        if not results["playlists"]["items"]:
            return f"No playlist found for {playlist_name}"

        playlist_uri = results["playlists"]["items"][0]["uri"]
        

        self.sp.shuffle(state=True, device_id=self.device_id)
        self.sp.start_playback(device_id=self.device_id, context_uri=playlist_uri)
        return results["playlists"]["items"][0]
