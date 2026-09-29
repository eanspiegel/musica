from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

_RADIO_PARAMS = {"start_radio", "radio"}

def _clean_url(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=False)
    list_id = (qs.get("list") or [""])[0]
    is_radio = list_id.startswith("RD") or any(p in qs for p in _RADIO_PARAMS)
    _STRIP = {"si", "pp", "index", "t", "start_radio", "radio", "feature"}
    cleaned = {}
    for key, values in qs.items():
        if key in _STRIP:
            continue
        if key == "list" and is_radio:
            continue
        cleaned[key] = values
    has_real_playlist = bool(list_id) and not is_radio
    if has_real_playlist and parsed.path in ("/watch", "/watch/"):
        host = parsed.scheme + "://" + (parsed.hostname or "www.youtube.com")
        return f"{host}/playlist?list={list_id}"
    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

tests = [
    ("OLAK playlist + v=",
     "https://www.youtube.com/watch?v=pH3zonR6M4g&list=OLAK5uy_mCgrBoTo9bxJc9fWIQE50nUUA6LMunPKQ",
     "https://www.youtube.com/playlist?list=OLAK5uy_mCgrBoTo9bxJc9fWIQE50nUUA6LMunPKQ"),
    ("Radio mix strips",
     "https://www.youtube.com/watch?v=_ZyD4n5zqxA&list=RD_ZyD4n5zqxA&start_radio=1&pp=oAcB",
     "https://www.youtube.com/watch?v=_ZyD4n5zqxA"),
    ("Real PL playlist",
     "https://www.youtube.com/watch?v=xyz&list=PLabc123&index=2&si=abc",
     "https://www.youtube.com/playlist?list=PLabc123"),
    ("Plain video no list",
     "https://www.youtube.com/watch?v=abc123",
     "https://www.youtube.com/watch?v=abc123"),
    ("Already playlist URL",
     "https://www.youtube.com/playlist?list=PLabc123",
     "https://www.youtube.com/playlist?list=PLabc123"),
    ("youtu.be short",
     "https://youtu.be/abc123",
     "https://youtu.be/abc123"),
]

all_ok = True
for name, inp, expected in tests:
    result = _clean_url(inp)
    ok = result == expected
    all_ok = all_ok and ok
    status = "OK" if ok else "FAIL"
    print(f"{status} [{name}]")
    if not ok:
        print(f"  expected: {expected}")
        print(f"  got:      {result}")

print()
print("All OK" if all_ok else "FAILURES FOUND")
