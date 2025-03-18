# from django.urls import path
# from .views import home, suggestions, spotify_login, spotify_callback, spotify_logout
# from . import views

# urlpatterns = [
#     path('', home, name='home'),  # This will serve the homepage
#     path('suggestions/', suggestions, name='suggestions'),
#     path("spotify/login/", views.spotify_login, name="spotify_login"),
#     path("spotify/callback/", views.spotify_callback, name="spotify_callback"),
#     path("spotify/logout/", spotify_logout, name="spotify_logout"),
# ]

from django.urls import path
from .views import get_audio_url, get_playlist_songs, get_suggestions, get_user_playlists, home, suggestions, spotify_login, spotify_callback, spotify_logout, search_songs

urlpatterns = [
    path('', home, name='home'),  # Home page with UI
    path('suggestions/', suggestions, name='suggestions'),
    path("suggestions/", get_suggestions, name="get_suggestions"),
    path("spotify/login/", spotify_login, name="spotify_login"),
    path("spotify/callback/", spotify_callback, name="spotify_callback"),
    path("spotify/logout/", spotify_logout, name="spotify_logout"),
    path("search/", search_songs, name="search_songs"),
    path('get_user_playlists/', get_user_playlists, name='get_user_playlists'),
    path('get_playlist_songs/<str:playlist_id>/', get_playlist_songs, name='get_playlist_songs'),
    path("get_audio_url/", get_audio_url, name="get_audio_url"),
]
