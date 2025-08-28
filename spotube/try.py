# yt_formats_test.py

from yt_dlp import YoutubeDL

url = "https://youtu.be/CKJA9blyMUg?si=NgJX5PJMTe0fX-mB"

with YoutubeDL({}) as ydl:
    info = ydl.extract_info(url, download=False)
    for f in info["formats"]:
        if f["vcodec"] == "none":  # Only audio formats
            print(f"{f['format_id']} - {f['ext']} - {f.get('acodec')} - {f['url']}")
