import yt_dlp
import json

url = "https://www.youtube.com/playlist?list=OLAK5uy_lQoW_Xp-P43hw81AR8LZW9pt1127Gpzvk"

opciones = {
    'quiet': True, 
    'no_warnings': True, 
    'extract_flat': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web']
        }
    }
}

print(f"Testing URL: {url}")
with yt_dlp.YoutubeDL(opciones) as ydl:
    info = ydl.extract_info(url, download=False)
    
    print(f"Type: {info.get('_type')}")
    print(f"Title: {info.get('title')}")
    if 'entries' in info:
        print(f"Entries found: {len(list(info['entries']))}")
    else:
        print("No entries key found.")
