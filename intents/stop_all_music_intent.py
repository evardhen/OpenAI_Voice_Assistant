import utils.global_variables as global_variables
from langchain_core.tools import tool

@tool("stop_all_music")
def stop_all_music_tool():
    """useful when you want to stop the music played over the assistant Luna."""
    return stop_all_music()

def stop_all_music():
    try:
        if global_variables.radio_player.is_playing():
            global_variables.radio_player.stop()
        if global_variables.spotify.is_spotify_playing():
            global_variables.spotify.stop()
        return "Successfully stopped playing music."
    except Exception as e:
        return f"Could not stop the music, an error occurred: {e}"
