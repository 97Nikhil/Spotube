from django.shortcuts import redirect
from django.http import JsonResponse
from .spotify import get_auth_url, get_token

# Step 1: Redirect user to Spotify login
def spotify_login(request):
    auth_url = get_auth_url()
    return redirect(auth_url)

# Step 2: Handle Spotify callback
def spotify_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "Authorization failed"}, status=400)

    token_data = get_token(code)
    return JsonResponse(token_data)  # You can store this in the session
