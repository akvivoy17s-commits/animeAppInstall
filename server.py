import os
import re
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote, unquote

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")

app = FastAPI(docs_url=None, redoc_url=None)

CACHE_SECONDS = 600
MAX_SHOTS = 5
_cache = {}          # key -> (time, value)
_img_cache = {}      # file_id -> (time, bytes, content_type)


def cached(key):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    return None


def store(key, value):
    _cache[key] = (time.time(), value)


# ---------- helpers ----------
def api_key() -> str:
    return os.getenv("DRIVE_API_KEY", "").strip()


def extract_file_id(raw: str):
    raw = (raw or "").strip()
    m = re.search(r"/d/([A-Za-z0-9_-]+)", raw) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", raw)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", raw):
        return raw
    return None


def extract_folder_id(raw: str):
    raw = (raw or "").strip()
    m = re.search(r"/folders/([A-Za-z0-9_-]+)", raw) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", raw)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{20,}", raw):
        return raw
    return None


def build_direct_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("DRIVE_URL is empty in .env")
    file_id = extract_file_id(raw)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return raw


def format_size(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / 1024 ** 3:.1f} GB"
    if n >= 1024 ** 2:
        v = n / 1024 ** 2
        return f"{v:.0f} MB" if v >= 100 else f"{v:.1f} MB"
    return f"{max(1, round(n / 1024))} KB"


def parse_version(name: Optional[str]) -> Optional[str]:
    """Pulls a version out of the file name: anime-portal-1.2.3.apk, AnimePortal_v2.apk ..."""
    if not name:
        return None
    m = re.search(r"(\d+(?:\.\d+){1,3})", name)
    if m:
        return m.group(1)
    m = re.search(r"[vV](\d+)", name)
    return m.group(1) if m else None


def filename_from_disposition(cd: str) -> Optional[str]:
    if not cd:
        return None
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd, re.I)
    if m:
        return unquote(m.group(1))
    m = re.search(r'filename="([^"]+)"', cd)
    return m.group(1) if m else None


# ---------- Drive lookups ----------
async def fetch_app_meta() -> dict:
    raw = os.getenv("DRIVE_URL", "")
    file_id = extract_file_id(raw)
    key = api_key()
    size = name = None

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        if file_id and key:
            r = await client.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                params={"fields": "size,name", "key": key},
            )
            if r.status_code == 200:
                j = r.json()
                size = int(j["size"]) if j.get("size") else None
                name = j.get("name")
            else:
                print(f"[drive] app info failed: HTTP {r.status_code} -> {r.text[:300]}")

        if size is None or name is None:
            async with client.stream("GET", build_direct_url(raw)) as r:
                ctype = r.headers.get("content-type", "")
                if not ctype.startswith("text/html"):
                    if size is None and r.headers.get("content-length"):
                        size = int(r.headers["content-length"])
                    if name is None:
                        name = filename_from_disposition(r.headers.get("content-disposition", ""))
    return {"size": size, "name": name}


async def get_screenshot_ids() -> list:
    hit = cached("shots")
    if hit is not None:
        return hit

    ids = []

    # 1) SCREENSHOT_1 ... SCREENSHOT_5 (empty ones are skipped)
    for i in range(1, MAX_SHOTS + 1):
        fid = extract_file_id(os.getenv(f"SCREENSHOT_{i}", ""))
        if fid and fid not in ids:
            ids.append(fid)

    # 2) SCREENSHOT_URLS (comma separated)
    if not ids:
        for part in os.getenv("SCREENSHOT_URLS", "").split(","):
            fid = extract_file_id(part)
            if fid and fid not in ids:
                ids.append(fid)

    # 3) Drive folder (needs DRIVE_API_KEY)
    if not ids:
        folder = extract_folder_id(os.getenv("SCREENSHOTS_FOLDER_URL", ""))
        key = api_key()
        if folder and key:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    params={
                        "q": f"'{folder}' in parents and mimeType contains 'image/' and trashed=false",
                        "orderBy": "name",
                        "pageSize": MAX_SHOTS,
                        "fields": "files(id,name)",
                        "key": key,
                    },
                )
                if r.status_code == 200:
                    ids = [f["id"] for f in r.json().get("files", [])]
                else:
                    print(f"[drive] screenshots failed: HTTP {r.status_code} -> {r.text[:300]}")

    ids = ids[:MAX_SHOTS]
    if ids:
        store("shots", ids)
    else:
        print("[drive] no screenshots found - check SCREENSHOT_1..5 / SCREENSHOT_URLS / SCREENSHOTS_FOLDER_URL in .env")
    return ids


# ---------- routes ----------
@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/logo.png")
def logo():
    return FileResponse(BASE / "logo.png")


@app.get("/api/app-info")
async def app_info():
    hit = cached("meta")
    if hit:
        return hit
    try:
        meta = await fetch_app_meta()
    except Exception as e:
        print(f"[drive] app info error: {e!r}")
        meta = {"size": None, "name": None}
    data = {
        "size_text": format_size(meta["size"]) if meta["size"] else None,
        "version": parse_version(meta["name"]),
    }
    if data["size_text"] or data["version"]:
        store("meta", data)
    return data


@app.get("/api/screenshots")
async def screenshots():
    try:
        ids = await get_screenshot_ids()
    except Exception as e:
        print(f"[drive] screenshots error: {e!r}")
        ids = []
    return {"images": [f"/screenshot/{i}" for i in ids]}


@app.get("/screenshot/{file_id}")
async def screenshot(file_id: str):
    # only serve files that are in our configured list (not an open proxy)
    if file_id not in await get_screenshot_ids():
        raise HTTPException(status_code=404)

    hit = _img_cache.get(file_id)
    if not hit or time.time() - hit[0] > 3600:
        key = api_key()
        r = None
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            if key:
                r = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    params={"alt": "media", "key": key},
                )
                if r.status_code != 200:
                    print(f"[drive] screenshot API failed {file_id}: {r.status_code} {r.text[:200]}")
                    r = None
            if r is None:  # fallback: no key, or key failed
                r = await client.get(
                    "https://drive.usercontent.google.com/download",
                    params={"id": file_id, "export": "download", "confirm": "t"},
                )
        ctype = r.headers.get("content-type", "")
        if r.status_code != 200 or not ctype.startswith("image/"):
            print(f"[drive] screenshot fetch failed {file_id}: {r.status_code} {ctype}")
            raise HTTPException(status_code=502, detail="Could not fetch image from Drive")
        hit = (time.time(), r.content, ctype)
        _img_cache[file_id] = hit

    return Response(hit[1], media_type=hit[2], headers={"Cache-Control": "public, max-age=3600"})


async def get_app_name() -> str:
    name = cached("name")
    if name:
        return name
    try:
        name = (await fetch_app_meta()).get("name")
    except Exception:
        name = None
    if name:
        store("name", name)
    return name or "AnimePortal.apk"


@app.get("/download")
async def download():
    raw = os.getenv("DRIVE_URL", "")
    file_id = extract_file_id(raw)
    if not file_id:
        raise HTTPException(status_code=500, detail="DRIVE_URL in .env is missing or invalid")

    key = api_key()
    if key:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        params = {"alt": "media", "key": key}
    else:
        # confirm=t skips Drive's "can't scan for viruses" page
        url = "https://drive.usercontent.google.com/download"
        params = {"id": file_id, "export": "download", "confirm": "t"}

    client = httpx.AsyncClient(timeout=httpx.Timeout(30, read=None), follow_redirects=True)
    try:
        req = client.build_request("GET", url, params=params)
        upstream = await client.send(req, stream=True)
    except Exception as e:
        await client.aclose()
        print(f"[drive] download error: {e!r}")
        raise HTTPException(status_code=502, detail="Could not reach Google Drive")

    ctype = upstream.headers.get("content-type", "")
    if upstream.status_code != 200 or ctype.startswith("text/html"):
        body = (await upstream.aread())[:300]
        await upstream.aclose()
        await client.aclose()
        print(f"[drive] download failed: HTTP {upstream.status_code} -> {body!r}")
        raise HTTPException(status_code=502, detail="Drive did not return the file (check sharing / API key)")

    name = filename_from_disposition(upstream.headers.get("content-disposition", "")) or await get_app_name()
    ascii_name = re.sub(r'[^A-Za-z0-9._-]', "_", name)
    headers = {
        "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}",
    }
    if upstream.headers.get("content-length"):
        headers["Content-Length"] = upstream.headers["content-length"]

    async def body():
        try:
            async for chunk in upstream.aiter_bytes(64 * 1024):
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(body(), media_type="application/vnd.android.package-archive", headers=headers)