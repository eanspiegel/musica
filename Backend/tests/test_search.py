import yt_dlp

opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'skip_download': True}
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info('ytsearch5:muse uprising', download=False)
    safe = ydl.sanitize_info(info) if info else {}
    print('Type:', safe.get('_type'))
    entries = safe.get('entries', [])
    for e in entries:
        print(f"- {e.get('title')} ({e.get('url')})")
