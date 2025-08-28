import yt_dlp
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth  # Add this import

sp = Spotify(auth_manager=SpotifyOAuth(
    client_id="9b8e5b654ede456085b9de0f5a991f9b",
    client_secret="8e504d8de6c9451b8cfc30e1c6da452c",
    redirect_uri="http://127.0.0.1:8000/spotify/callback/",
    scope="user-library-read user-read-playback-state user-modify-playback-state"
))



def fetch_songs_from_spotify(playlist_id):
    """
    Fetches all songs from a given Spotify playlist ID.
    """
    try:
        results = sp.playlist_tracks(playlist_id)
        songs = []
        
        for item in results['items']:
            track = item['track']
            songs.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'spotify_url': track['external_urls']['spotify'],
                'duration_ms': track['duration_ms']
            })

        return songs
    except Exception as e:
        print(f"Error fetching playlist songs: {e}")
        return []

def get_audio_url(spotify_url):
    """
    Fetches the audio URL of a song from YouTube using yt-dlp.
    :param spotify_url: The Spotify track URL.
    :return: The direct audio URL (or None if not found).
    """
    search_query = f"{spotify_url}"  # You might need to extract the song name instead

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
            if 'entries' in search_results and search_results['entries']:
                video_url = search_results['entries'][0]['url']  # Get the first result
                return video_url
        except Exception as e:
            print(f"Error fetching audio URL: {e}")

    return None
