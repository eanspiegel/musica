# Technical Debt — Migration Analysis

> **Scope**: Current monolithic Python/Tkinter codebase prior to FastAPI + Vue migration.  
> All items are evidence-based — each one references specific files and line numbers.  
> Priority order: **CRITICAL → HIGH → MEDIUM → LOW**

---

## Priority Legend

| Symbol | Priority | Meaning |
|---|---|---|
| 🔴 | **CRITICAL** | Blocks security, data integrity, or the migration itself |
| 🟠 | **HIGH** | Significant risk or architectural violation |
| 🟡 | **MEDIUM** | Technical quality, maintainability, or best-practice gap |
| 🟢 | **LOW** | Nice-to-have, cleanup, or future-proofing |

---

## Complexity Legend

| Symbol | Complexity | Effort |
|---|---|---|
| ⚡ | **Simple** | Isolated change, no cross-cutting impact |
| 🔧 | **Moderate** | Touches multiple files, requires planning |
| 🏗️ | **High** | Architectural refactor, needs dedicated sprint |

---

## Items

---

### 🔴 TD-01 — Bare `except:` blocks swallow all errors silently

**Priority**: CRITICAL | **Complexity**: ⚡ Simple | **Estimated time**: 2–3 h

**Problem**  
Multiple `except:` (no exception type, no logging) are used throughout the codebase.

```
youtube_service.py:41   → except: pass  (URL parsing)
youtube_service.py:59   → except: pass  (playlist ID extraction)
youtube_service.py:86   → except: pass  (thumbnail fetch)
youtube_service.py:292  → except: pass  (progress parsing)
metadata_service.py:58  → except: pass  (year parsing)
metadata_service.py:307 → except: pass  (Deezer track detail)
metadata_service.py:312 → except: pass  (entire Deezer fallback loop)
```

**What it causes**  
- Failures are invisible in production — no way to diagnose what went wrong
- Network errors, timeouts, and API failures are silently discarded
- Impossible to distinguish a "no result" from a "crashed" scenario
- The migration to FastAPI will surface these as 500s with no useful context

**How to fix**  
Replace every bare `except` with typed catches and structured logging.  
In the new backend, use a centralized error handler middleware and `logging` (not `print`).

```python
# Before
except:
    pass

# After
except (requests.Timeout, requests.ConnectionError) as exc:
    logger.warning("iTunes request failed", exc_info=exc)
```

---

### 🔴 TD-02 — No rate limiting on outbound API calls (Shazam, iTunes, Deezer, LRCLIB)

**Priority**: CRITICAL | **Complexity**: 🔧 Moderate | **Estimated time**: 4–6 h

**Problem**  
`metadata_service.py` and `tags_search_service.py` call external APIs inside `ThreadPoolExecutor` workers with no throttling.  
Batch downloads (`playlist_service.py:61`) run 2 concurrent workers, each independently calling iTunes, Deezer, and LRCLIB per song.

**What it causes**  
- iTunes API (undocumented rate limit) will start returning 403/429 for heavy playlists
- Deezer enforces 50 req/5s per IP — easily exceeded on a 20-song playlist batch
- LRCLIB is a community-maintained service — hammering it is unethical and will get the IP banned
- In a FastAPI backend exposed over the network, this becomes a vector for **amplification attacks**: one user request can trigger dozens of outbound calls

**How to fix**  
Implement a token-bucket or sliding-window rate limiter per external provider.  
Use `asyncio.Semaphore` in the new async adapters:

```python
# In each adapter
_itunes_semaphore = asyncio.Semaphore(5)  # max 5 concurrent calls

async def search(self, query: str) -> dict:
    async with _itunes_semaphore:
        await asyncio.sleep(0.2)  # min 200ms between calls
        return await self._http_get(...)
```

For the FastAPI layer, also add **inbound** rate limiting per IP using `slowapi` (based on `limits`).

---

### 🔴 TD-03 — No input validation on URLs — SSRF vector

**Priority**: CRITICAL | **Complexity**: 🔧 Moderate | **Estimated time**: 3–4 h

**Problem**  
`youtube_service.py:45` (`obtener_info_basica`) and `descargar` receive a raw URL string and pass it directly to `yt_dlp.YoutubeDL`. There is no allowlist validation.

**What it causes**  
- **Server-Side Request Forgery (SSRF)**: once this is a FastAPI endpoint, an attacker can pass `http://169.254.169.254/latest/meta-data/` (AWS metadata endpoint) or any internal network address
- `yt_dlp` supports many extractors including local files (`file://`), FTP, and arbitrary protocols
- An attacker can enumerate internal services from the backend server

**How to fix**  
Validate URL scheme and hostname BEFORE passing to yt-dlp:

```python
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https", "http"}
ALLOWED_HOSTS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "music.youtube.com",
}

def validate_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Scheme not allowed: {parsed.scheme}")
    if parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Host not allowed: {parsed.hostname}")
    return url
```

Also disable yt-dlp's `file://` and internal extractors via `allowed_extractors`.

---

### 🔴 TD-04 — Synchronous HTTP inside async context using `asyncio.to_thread`

**Priority**: CRITICAL | **Complexity**: 🔧 Moderate | **Estimated time**: 4–5 h

**Problem**  
`metadata_service.py` uses `requests` (a blocking sync library) wrapped in `asyncio.to_thread` to simulate async behavior.

```python
# metadata_service.py:104
resp = await asyncio.to_thread(requests.get, url, params=params, timeout=5)

# metadata_service.py:209
resp = await asyncio.to_thread(requests.get, url_itunes, timeout=5)
```

**What it causes**  
- Each `to_thread` call spawns a thread from the default thread pool — under load this exhausts the pool
- In FastAPI's async event loop, this blocks the loop thread pool and degrades throughput for ALL requests
- `requests.Session` is not thread-safe when shared — connection pooling breaks

**How to fix**  
Replace `requests` with `httpx` (async-native) in all adapters:

```python
import httpx

async def search(self, query: str) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
```

Use a shared `httpx.AsyncClient` per adapter (not per-request) for connection pooling.

---

### 🔴 TD-05 — `asyncio.run()` called inside a method that may already be in an event loop

**Priority**: CRITICAL | **Complexity**: ⚡ Simple | **Estimated time**: 1–2 h

**Problem**  
`metadata_service.py:477` calls `asyncio.run()` inside a synchronous method:

```python
def etiquetar(self, ...):
    return asyncio.run(self._etiquetar_async(...))
```

And `tags_search_service.py:184–187` creates and closes an event loop manually:

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
resultado_shazam = loop.run_until_complete(self.reconocer_con_shazam(ruta_archivo))
loop.close()
```

**What it causes**  
- `asyncio.run()` throws `RuntimeError: This event loop is already running` when called from FastAPI's async context (which always has a running loop)
- The manual loop in `tags_search_service.py` leaks if an exception occurs before `loop.close()`
- These two patterns cannot coexist in an async FastAPI application without a rewrite

**How to fix**  
All async logic must be made natively async — no sync wrappers.  
In FastAPI, everything runs in the same event loop, so `await service.etiquetar(...)` is the correct pattern.

---

### 🟠 TD-06 — Zero separation between third-party libraries and business logic

**Priority**: HIGH | **Complexity**: 🏗️ High | **Estimated time**: 2–3 days

**Problem**  
`metadata_service.py` directly imports `mutagen`, `requests`, `shazamio` at the top level and uses them inline in business logic.  
`youtube_service.py` directly instantiates and configures `yt_dlp.YoutubeDL` inline.  
`tags_search_service.py` imports `requests` and `shazamio` at the same level as business logic.

**What it causes**  
- No library can be swapped without rewriting business logic
- Impossible to unit-test services without running real network calls
- The new architecture's adapter pattern (defined in `BackEnd/README.md`) cannot be applied incrementally — it requires extracting every library call first

**How to fix**  
This is the core migration task. Each lib gets its own adapter implementing a port (interface):
- `mutagen` → `MutagenAdapter(ITagWriter)`
- `shazamio` → `ShazamAdapter(IAudioRecognition)`
- `yt_dlp` → `YtDlpAdapter(IDownloader)`
- `requests` calls to iTunes/Deezer/LRCLIB → separate `*Adapter(IMetadataProvider)`

Services then depend ONLY on the port protocol, not the lib.

---

### 🟠 TD-07 — State shared via instance variable (`video_data_cache`) in the controller

**Priority**: HIGH | **Complexity**: 🔧 Moderate | **Estimated time**: 4–6 h

**Problem**  
`app_controller.py:18` stores the last analyzed URL result on the instance:

```python
self.video_data_cache = None  # app_controller.py:18
...
self.video_data_cache = data  # app_controller.py:33
```

This cache is then read directly in `start_download` and `start_download_thread`.

**What it causes**  
- In a multi-user FastAPI scenario, this is a **race condition**: User A's analyze result can overwrite User B's before their download starts
- There is no invalidation strategy — stale data can persist indefinitely
- The single-download path (`start_download_thread:60`) has a `pass` where actual download logic should be, meaning the cache may be consumed incorrectly

**How to fix**  
In the new backend:
- Generate a `job_id` (UUID) when the URL is analyzed
- Store the analysis result keyed by `job_id` in an in-memory store or cache (e.g., `dict` with TTL)
- The download request must carry the `job_id` — never rely on implicit shared state

---

### 🟠 TD-08 — No CORS policy, no authentication, no API key strategy

**Priority**: HIGH | **Complexity**: 🔧 Moderate | **Estimated time**: 3–4 h

**Problem**  
The current codebase is a desktop app with no network layer, so this is not a current vulnerability.  
However, the migration to FastAPI + Vue makes this a day-one requirement:
- No CORS configuration defined
- No authentication mechanism planned
- No API key or token strategy for the backend

**What it causes**  
- Without CORS, the browser will block all frontend requests to the backend
- Without any auth, the FastAPI backend is publicly accessible — anyone who knows the URL can trigger downloads and filesystem writes
- Without rate limiting + auth combined, the backend can be used as a download proxy by third parties

**How to fix**  
- **CORS**: Define `cors_origins` in `Settings` (already in `BackEnd/README.md`) and configure `CORSMiddleware` in FastAPI
- **Auth**: For a local/personal tool, a single static API key in headers (`X-API-Key`) is sufficient and zero-friction
- **Minimum config**:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
)
```

---

### 🟠 TD-09 — Duplicate Shazam recognition logic in two services

**Priority**: HIGH | **Complexity**: ⚡ Simple | **Estimated time**: 2 h

**Problem**  
Shazam recognition logic is copy-pasted identically between:
- `metadata_service.py:25–89` → `_buscar_shazam()`
- `tags_search_service.py:21–89` → `reconocer_con_shazam()`

Both create a new `Shazam()` instance per call, parse the exact same response shape, and return nearly identical dicts.

**What it causes**  
- Any change to the Shazam API response format requires fixing two places
- The `ShazamAdapter` defined in the migration architecture will have to reconcile two different output shapes
- Bugs fixed in one copy remain in the other

**How to fix**  
The `ShazamAdapter` is the single authoritative Shazam consumer. Both services get replaced by a call to the same adapter.

---

### 🟠 TD-10 — `nocheckcertificate: True` in yt-dlp options

**Priority**: HIGH | **Complexity**: ⚡ Simple | **Estimated time**: 30 min

**Problem**  
`youtube_service.py:302`:
```python
'nocheckcertificate': True,
```

**What it causes**  
- Disables TLS certificate verification for all yt-dlp network requests
- Makes the download process vulnerable to Man-in-the-Middle attacks — the content downloaded could be tampered with
- This was added as a workaround for a connection issue, not for a legitimate reason

**How to fix**  
Remove this option. If TLS errors occur in specific environments, handle them explicitly per-environment via the `requests` CA bundle or yt-dlp's `legacyserverconnect` option — never by disabling verification globally.

---

### 🟡 TD-11 — `print()` used as the only logging mechanism

**Priority**: MEDIUM | **Complexity**: ⚡ Simple | **Estimated time**: 2–3 h

**Problem**  
All observability in the codebase is done via `print()`. There are 40+ `print()` calls across services, controllers, and adapters. Some include emojis, some are debug-only, none have severity levels.

**What it causes**  
- No way to filter by severity (debug vs. error vs. warning)
- No structured output for log aggregators (e.g., Loki, Datadog, CloudWatch)
- Debug prints will appear in production stdout alongside real errors
- FastAPI's default logging setup is overridden/ignored

**How to fix**  
Replace all `print()` with Python's standard `logging` module, configured at the application level:

```python
import logging
logger = logging.getLogger(__name__)

# Usage
logger.debug("URL cleaned: %s", clean_url)
logger.warning("Shazam recognition failed for: %s", file_path)
logger.error("yt-dlp download failed", exc_info=True)
```

Configure log level via the `LOG_LEVEL` env var in `Settings`.

---

### 🟡 TD-12 — `config.json` stored next to the source code / executable

**Priority**: MEDIUM | **Complexity**: ⚡ Simple | **Estimated time**: 1 h

**Problem**  
`config_manager.py:11–12`:
```python
self.config_file = 'config.json'
self.base_path = self._obtener_ruta_base()  # returns dirname of config_manager.py
```

**What it causes**  
- In the new backend, this path is meaningless (FastAPI runs as a server, not an executable)
- Configuration next to source is an anti-pattern — it gets overwritten on deploys
- There is no schema validation on `config.json` — malformed files silently return `None`

**How to fix**  
All configuration moves to environment variables via `pydantic-settings`.  
`config.json` is deprecated. Persist user preferences (download path, etc.) in a proper settings store or pass them per-request.

---

### 🟡 TD-13 — `_es_artista_valido` is a stub that always returns `True`

**Priority**: MEDIUM | **Complexity**: 🔧 Moderate | **Estimated time**: 3–4 h

**Problem**  
`metadata_service.py:373–375`:
```python
def _es_artista_valido(self, ...) -> bool:
    if not artist_found: return False
    return True  # "Asumimos validación externa o permisiva por ahora"
```

This function is supposed to validate that the artist found by iTunes/Deezer matches the expected artist. It has been stubbed out with a comment indicating it was intentionally disabled.

**What it causes**  
- The `strict_artist_match` parameter that flows through `etiquetar()` and `start_download()` has no effect
- Songs are tagged with incorrect artists because the validation that should reject mismatches always returns `True`
- The "impostor correction" logic in `playlist_service.py:132–145` compensates for this failure downstream — creating circular complexity

**How to fix**  
Implement the real validation using normalized string comparison and the existing `_es_coincidencia_valida` pattern.

---

### 🟡 TD-14 — Concurrency model mixes `threading` and `asyncio` without a clear boundary

**Priority**: MEDIUM | **Complexity**: 🏗️ High | **Estimated time**: 1 day

**Problem**  
The codebase uses:
- `threading.Thread` in `app_controller.py:68,115` for download tasks
- `concurrent.futures.ThreadPoolExecutor` in `playlist_service.py:61` for batch downloads
- `asyncio` + `asyncio.to_thread` in `metadata_service.py` for API calls
- `asyncio.new_event_loop()` + `loop.close()` in `tags_search_service.py:184`

These four concurrency models are used without coordination.

**What it causes**  
- In FastAPI (single event loop), `threading.Thread` for I/O is an anti-pattern — it bypasses the event loop and causes backpressure issues
- The mixed model makes it impossible to implement proper cancellation or timeouts
- The `status_callback` passed into threaded workers is called from background threads and updates UI state — thread-unsafe

**How to fix**  
In the new backend: **one concurrency model — `asyncio` exclusively**.  
- Download tasks → `asyncio` background tasks (`asyncio.create_task`)  
- Progress reporting → SSE (Server-Sent Events) or WebSocket endpoint
- Batch processing → `asyncio.gather` with a semaphore to cap concurrency

---

### 🟡 TD-15 — Filesystem writes with no path traversal protection

**Priority**: MEDIUM | **Complexity**: ⚡ Simple | **Estimated time**: 2 h

**Problem**  
`youtube_service.py:298`:
```python
'outtmpl': os.path.join(directorio, '%(title)s.%(ext)s'),
```

The `%(title)s` token comes from the YouTube video title, which can contain `../` sequences, absolute paths, or special characters that break filenames on Windows/Linux differently.

`metadata_service.py:342` sanitizes before rename, but the download itself is unsanitized.

**What it causes**  
- A malicious video title like `../../etc/cron.d/backdoor` could write files outside the intended download directory
- On the API layer, a user-controlled `directorio` parameter combined with a malicious title is a **path traversal vulnerability**

**How to fix**  
```python
import pathlib

def safe_output_template(base_dir: str) -> str:
    resolved = pathlib.Path(base_dir).resolve()
    # Validate resolved is within allowed root
    if not str(resolved).startswith(str(settings.allowed_download_root)):
        raise ValueError("Download path outside allowed root")
    return str(resolved / "%(title)s.%(ext)s")
```

yt-dlp also has `restrictfilenames: True` — enable it to sanitize titles automatically.

---

### 🟢 TD-16 — No retry strategy with exponential backoff for external API calls

**Priority**: LOW | **Complexity**: ⚡ Simple | **Estimated time**: 2 h

**Problem**  
All external HTTP calls in `metadata_service.py` and `tags_search_service.py` use a flat `timeout=5` or `timeout=10` with no retry logic. A transient 503 from iTunes or Deezer results in an immediate silent failure.

**How to fix**  
Use `httpx` with `tenacity` for declarative retry:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4))
async def _fetch(self, url: str) -> dict:
    ...
```

---

### 🟢 TD-17 — Thumbnail fetch creates a nested `yt_dlp.YoutubeDL` instance inside another

**Priority**: LOW | **Complexity**: ⚡ Simple | **Estimated time**: 1 h

**Problem**  
`youtube_service.py:83–86`:
```python
with yt_dlp.YoutubeDL({'quiet': True}) as ydl_thumb:
    info_thumb = ydl_thumb.extract_info(first_entry['url'], download=False)
```

This is called inside an outer `with yt_dlp.YoutubeDL(opciones) as ydl:` block.

**What it causes**  
- Two yt-dlp instances open simultaneously, each consuming memory and potentially conflicting on shared yt-dlp state
- An extra network round-trip per playlist for what could be derived from the video ID

**How to fix**  
Use the YouTube thumbnail URL formula instead of a second extraction:
```python
thumbnail = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
```

---

### 🟢 TD-18 — `_clean_url` duplicates its own parsing logic

**Priority**: LOW | **Complexity**: ⚡ Simple | **Estimated time**: 1 h

**Problem**  
`youtube_service.py:17–43`: The `if 'list=' in url and 'v=' in url:` check is performed TWICE — once for the radio/mix case (lines 19–29) and once again for the playlist case (lines 31–40), with identical `urlparse` / `parse_qs` calls inside both branches.

**What it causes**  
- Code duplication that diverges over time
- The URL is parsed 2–3 times for the same input

**How to fix**  
Parse once, then branch on the parsed values.

---

## Summary Table

| ID | Title | Priority | Complexity | Est. Time |
|---|---|---|---|---|
| TD-01 | Bare `except:` blocks | 🔴 CRITICAL | ⚡ | 2–3 h |
| TD-02 | No rate limiting on outbound APIs | 🔴 CRITICAL | 🔧 | 4–6 h |
| TD-03 | No URL validation — SSRF vector | 🔴 CRITICAL | 🔧 | 3–4 h |
| TD-04 | Sync `requests` inside async context | 🔴 CRITICAL | 🔧 | 4–5 h |
| TD-05 | `asyncio.run()` inside async context | 🔴 CRITICAL | ⚡ | 1–2 h |
| TD-06 | Zero lib/business logic separation | 🟠 HIGH | 🏗️ | 2–3 days |
| TD-07 | Shared mutable state in controller | 🟠 HIGH | 🔧 | 4–6 h |
| TD-08 | No CORS / auth / API key strategy | 🟠 HIGH | 🔧 | 3–4 h |
| TD-09 | Duplicate Shazam logic | 🟠 HIGH | ⚡ | 2 h |
| TD-10 | `nocheckcertificate: True` | 🟠 HIGH | ⚡ | 30 min |
| TD-11 | `print()` as logging | 🟡 MEDIUM | ⚡ | 2–3 h |
| TD-12 | `config.json` next to source | 🟡 MEDIUM | ⚡ | 1 h |
| TD-13 | `_es_artista_valido` always returns `True` | 🟡 MEDIUM | 🔧 | 3–4 h |
| TD-14 | Mixed concurrency model | 🟡 MEDIUM | 🏗️ | 1 day |
| TD-15 | Path traversal on download output | 🟡 MEDIUM | ⚡ | 2 h |
| TD-16 | No retry/backoff for external APIs | 🟢 LOW | ⚡ | 2 h |
| TD-17 | Nested yt-dlp instances for thumbnail | 🟢 LOW | ⚡ | 1 h |
| TD-18 | Duplicate URL parsing in `_clean_url` | 🟢 LOW | ⚡ | 1 h |

---

## Total Estimated Effort

| Category | Items | Time |
|---|---|---|
| 🔴 CRITICAL | 5 | ~15–20 h |
| 🟠 HIGH | 5 | ~12–16 h + 2–3 days |
| 🟡 MEDIUM | 5 | ~9–12 h + 1 day |
| 🟢 LOW | 3 | ~4 h |
| **Total** | **18** | **~5–7 working days** |

> The 🔴 CRITICAL items are **migration blockers** — they must be resolved in the new codebase, not carried forward.  
> The 🟠 HIGH items are **first sprint** of the migration.  
> 🟡 and 🟢 items can be addressed progressively as each module is migrated.
