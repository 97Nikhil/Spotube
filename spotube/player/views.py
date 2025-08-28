import logging
import os
import json
import requests
from django.conf import settings
from urllib.parse import urlencode
from django.shortcuts import redirect
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import yt_dlp
from .spotify_api import get_audio_url
from .spotify_api import fetch_songs_from_spotify


redirect_uri = settings.SPOTIFY_REDIRECT_URI
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_API_URL = "https://api.spotify.com/v1"



def get_spotify_access_token(request):
    """Get a valid Spotify access token, refreshing if expired."""
    access_token = request.session.get("spotify_access_token")
    refresh_token = request.session.get("spotify_refresh_token")
    
    if not access_token:
        print("❌ No access token found.")
        return None

    # ✅ Check if token is still valid
    headers = {"Authorization": f"Bearer {access_token}"}
    test_url = "https://api.spotify.com/v1/me"
    response = requests.get(test_url, headers=headers)
    
    if response.status_code == 401 and refresh_token:
        print("🔄 Access token expired. Refreshing token...")

        # Spotify API requires client credentials to refresh token
        auth_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.SPOTIFY_CLIENT_ID,
            "client_secret": settings.SPOTIFY_CLIENT_SECRET,
        }

        refresh_response = requests.post(SPOTIFY_TOKEN_URL, data=auth_data)
        refresh_json = refresh_response.json()

        if "access_token" in refresh_json:
            new_access_token = refresh_json["access_token"]
            request.session["spotify_access_token"] = new_access_token
            print("✅ New token obtained:", new_access_token[:10] + "...")  # Print partial token for security
            return new_access_token
        else:
            print("❌ Failed to refresh token:", refresh_json)
            return None

    return access_token


def fetch_spotify_suggestions(access_token):
    """Fetch suggested songs from Spotify (e.g., from featured playlists)."""
    headers = {"Authorization": f"Bearer {access_token}"}
    suggested_tracks = []

    try:
        # ✅ Step 1: Get Featured Playlists
        response = requests.get(f"{SPOTIFY_API_URL}/browse/featured-playlists", headers=headers)
        print("\n📢 Featured Playlists API Response:", response.status_code, response.text)  # 🔍 Debugging

        if response.status_code == 200:
            playlists = response.json().get("playlists", {}).get("items", [])

            if not playlists:
                print("❌ No featured playlists found.")
                return []

            # ✅ Step 2: Get tracks from the first playlist
            playlist_id = playlists[0]["id"]
            print(f"🎵 Using Playlist ID: {playlist_id}")

            track_response = requests.get(f"{SPOTIFY_API_URL}/playlists/{playlist_id}/tracks", headers=headers)
            print("\n🎵 Playlist Tracks API Response:", track_response.status_code, track_response.text)  # 🔍 Debugging

            if track_response.status_code == 200:
                tracks = track_response.json().get("items", [])[:5]  # Get first 5 tracks
                if not tracks:
                    print("❌ No tracks found in playlist.")
                    return []

                for item in tracks:
                    track = item.get("track", {})
                    if track:
                        suggested_tracks.append({
                            "name": track.get("name", "Unknown Song"),
                            "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown Artist",
                            "image_url": track["album"]["images"][0]["url"] if track["album"].get("images") else "",
                        })
            else:
                print("❌ Failed to fetch tracks from playlist.")
    except Exception as e:
        print(f"❌ Error fetching Spotify suggestions: {e}")

    print("\n📌 Final Suggested Tracks:", suggested_tracks)  # 🔍 Final output
    return suggested_tracks


def fetch_search_results(query, access_token):
    """Fetch search results from Spotify."""
    headers = {"Authorization": f"Bearer {access_token}"}
    search_result = None

    try:
        search_url = f"{SPOTIFY_API_URL}/search?q={query}&type=track&limit=1"
        response = requests.get(search_url, headers=headers)
        print("\n🔍 Search API Response:", response.status_code, response.text)  # ✅ Print response

        if response.status_code == 200:
            tracks = response.json().get("tracks", {}).get("items", [])
            if tracks:
                track = tracks[0]
                search_result = {
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
                }
                print("✅ Search Result:", search_result)  # ✅ Print fetched song details
    except Exception as e:
        print(f"❌ Error fetching search results: {e}")

    return search_result

logger = logging.getLogger(__name__)

def suggestions(request):
    query = request.GET.get("q", "").strip()
    access_token = get_spotify_access_token(request)

    if not access_token:
        return JsonResponse({"error": "You must be logged in to view suggestions."}, status=401)

    logger.info(f"Received search query: {query}")  # ✅ Check if the query is received

    suggested_tracks = fetch_spotify_suggestions(access_token)
    search_result = fetch_search_results(query, access_token) if query else None

    logger.info(f"Search Result: {search_result}")  # ✅ Log what search_result returns

    # 🔍 Print Final API Response Before Returning
    print("\n🛠 Final API Response:", {"suggestions": suggested_tracks, "search_result": search_result})

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"suggestions": suggested_tracks, "search_result": search_result})

    return render(request, "player/index.html", {"suggestions": suggested_tracks, "search_result": search_result})


# Home
def home(request):
    """Render the main player UI with authentication status."""
    context = {
        "is_logged_in": "spotify_access_token" in request.session,
    }
    return render(request, "player/index.html", context)

def spotify_profile(request):
    access_token = request.session.get("spotify_access_token")

    if not access_token:
        return redirect("spotify_login")

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    
    if response.status_code != 200:
        return render(request, 'player/error.html', {"error": "Failed to fetch profile."})

    user_data = response.json()
    return render(request, "player/profile.html", {"user": user_data})

def spotify_login(request):
    params = {
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "response_type": "code",
        "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
        "scope": "user-library-read user-read-playback-state user-modify-playback-state",
    }
    return redirect(f"{SPOTIFY_AUTH_URL}?{urlencode(params)}")

def spotify_callback(request):
    """Handle Spotify callback and exchange code for access token."""
    code = request.GET.get("code")  # Get the authorization code from the callback URL
    
    if not code:
        return redirect("home")  # If there's no code, redirect to home page

    # Spotify token request
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "client_secret": settings.SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(token_url, data=payload, headers=headers)
    token_info = response.json()

    if "access_token" not in token_info:
        return redirect("home")  # Redirect to home if token fetch fails

    # Store access token in session (or database if needed)
    request.session["spotify_access_token"] = token_info["access_token"]
    request.session["spotify_refresh_token"] = token_info["refresh_token"]
    request.session["spotify_expires_in"] = token_info["expires_in"]

    return redirect("home")  # Redirect user to home page

def spotify_logout(request):
    """Logout user by clearing Spotify session data."""
    request.session.pop("spotify_access_token", None)
    request.session.pop("spotify_refresh_token", None)
    request.session.pop("spotify_expires_in", None)

    return redirect("home")  # Redirect to home after logout

def search_songs(request):
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"error": "Missing query"}, status=400)

    access_token = settings.SPOTIFY_ACCESS_TOKEN
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=12"  # ✅ Fetch 12 results
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch data from Spotify"}, status=response.status_code)

    data = response.json()

    # ✅ Extract up to 12 tracks
    tracks = data.get("tracks", {}).get("items", [])

    # ✅ Format the response properly
    suggestions = []
    for track in tracks:
        song_data = {
            "name": track["name"],
            "artist": ", ".join([artist["name"] for artist in track["artists"]]),
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
            "spotify_url": track["external_urls"]["spotify"]
        }
        suggestions.append(song_data)

    return JsonResponse({"suggestions": suggestions})


def fetch_user_playlists(access_token):
    """Fetch user's Spotify playlists."""
    headers = {"Authorization": f"Bearer {access_token}"}
    playlists = []

    try:
        response = requests.get(f"{SPOTIFY_API_URL}/me/playlists", headers=headers)

        if response.status_code == 200:
            data = response.json()
            for playlist in data.get("items", []):
                playlists.append({
                    "id": playlist["id"],
                    "name": playlist["name"],
                    "image_url": playlist["images"][0]["url"] if playlist["images"] else "",
                })
    except Exception as e:
        print(f"❌ Error fetching playlists: {e}")

    return playlists


def get_user_playlists(request):
    """API to fetch user playlists."""
    access_token = get_spotify_access_token(request)
    if not access_token:
        return JsonResponse({"error": "You must be logged in."}, status=401)

    playlists = fetch_user_playlists(access_token)
    return JsonResponse({"playlists": playlists})

import requests

def get_songs_from_spotify(playlist_id, access_token):
    """
    Fetch songs from a Spotify playlist.
    """
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching playlist songs: {response.json()}")
        return []

    data = response.json()
    songs = []

    for item in data.get("items", []):
        track = item.get("track", {})
        if track:
            songs.append({
                "id": track["id"],
                "name": track["name"],
                "artist": ", ".join(artist["name"] for artist in track["artists"]),
                "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
                "spotify_url": track["external_urls"]["spotify"]
            })
    
    return songs

def search_youtube_for_song(song_name, artist):
    """
    Search for a song on YouTube and return the best matching video URL.
    """
    query = f"{song_name} {artist} official audio"  # Improve search accuracy
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch:{query}", download=False)
            if "entries" in search_results and search_results["entries"]:
                video_url = search_results["entries"][0]["webpage_url"]
                return video_url
        except Exception as e:
            print(f"Error searching YouTube: {e}")
    
    return None  # Return None if no result found


def fetch_playlist_songs(playlist_id, access_token):
    try:
        print(f"Fetching songs for playlist: {playlist_id}")
        
        spotify_songs = get_songs_from_spotify(playlist_id, access_token)
        print(f"Spotify songs fetched: {spotify_songs}")

        for song in spotify_songs:
            youtube_url = search_youtube_for_song(song["name"], song["artist"])  
            print(f"Found YouTube URL: {youtube_url}")
            
            song["audio_url"] = get_audio_url(youtube_url)  
            print(f"Extracted Audio URL: {song['audio_url']}")

        return spotify_songs
    except Exception as e:
        print(f"Error fetching playlist songs: {e}")
        return []



def get_playlist_songs(request, playlist_id):
    access_token = get_spotify_access_token(request)
    if not access_token:
        return JsonResponse({"error": "You must be logged in."}, status=401)

    songs = fetch_playlist_songs(playlist_id, access_token)

    print("Fetched songs:", songs)  # ✅ Debugging

    return JsonResponse({"songs": songs})



def get_audio_url(youtube_url):
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",  
        "quiet": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"] if "url" in info else None
    
def get_suggestions(request):
    query = request.GET.get("q", "")
    if not query:
        return JsonResponse({"error": "No query provided"}, status=400)

    # Example response (replace with actual logic)
    data = {
        "search_result": {
            "name": "Example Song",
            "artist": "Example Artist",
            "image_url": "https://example.com/image.jpg",
            "audio_url": "https://example.com/audio.mp3",
        },
        "suggestions": [],
    }
    return JsonResponse(data)

import yt_dlp

def extract_audio_url(youtube_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'skip_download': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            return info_dict['url']
    except Exception as e:
        print(f"❌ yt-dlp error while extracting audio: {e}")
        return None
