#!/usr/bin/env python3
import io, os, sys, time, glob, fnmatch, json, hashlib, logging, threading
from datetime import datetime, timedelta
from urllib.parse import quote
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

import yaml
from flask import Flask, send_file, jsonify, request, abort
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

import pychromecast
from dateutil import parser as dateparser
import exifread

# Optional deps
try:
    import boto3
except Exception:
    boto3 = None
try:
    from webdav3.client import Client as WebDAVClient
except Exception:
    WebDAVClient = None

app = Flask(__name__)

# -------- Config / Logging ----------
CFG = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "config.yaml")))
LOG_LEVEL = getattr(logging, CFG.get("logging", {}).get("level", "INFO"))
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(CFG.get("logging", {}).get("file", "/tmp/photocastd.log"))
    ]
)
log = logging.getLogger("photocastd")

CACHE_DIR = "/tmp/photocastd-cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# -------- Data structures ----------
@dataclass
class MediaItem:
    id: str
    source: str     # local|webdav|s3
    path: str       # local path, or webdav path, or s3 key
    mtime: float
    size: int
    filename: str

PLAYLIST: List[MediaItem] = []
PLAYHEAD = 0
CAST_THREADS: Dict[str, threading.Thread] = {}
CAST_STOP_FLAGS: Dict[str, threading.Event] = {}

LONG_EDGE = CFG.get("render", {}).get("long_edge", 1920)
JPEG_Q = CFG.get("render", {}).get("jpeg_quality", 88)

CAPTION = CFG.get("render", {}).get("caption", {}).get("enabled", False)
CAPTION_TEXT = CFG.get("render", {}).get("caption", {}).get("text", "{datetime} · {filename}")
FONT_PATH = CFG.get("render", {}).get("caption", {}).get("font_path")
FONT_SIZE = CFG.get("render", {}).get("caption", {}).get("font_size", 28)
CAPTION_SHADOW = CFG.get("render", {}).get("caption", {}).get("shadow", True)

BASE_URL = CFG.get("server", {}).get("base_url")

# -------- Helpers ----------
def hash_id(source: str, path: str) -> str:
    return hashlib.sha1(f"{source}:{path}".encode()).hexdigest()[:16]

def exif_datetime(local_path: str) -> Optional[str]:
    try:
        with open(local_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal", details=False)
        dt = tags.get("EXIF DateTimeOriginal") or tags.get("Image DateTime")
        if dt:
            # format "YYYY:MM:DD HH:MM:SS"
            return str(dt).replace(":", "-", 2)
    except Exception:
        pass
    return None

def ensure_font():
    try:
        return ImageFont.truetype(FONT_PATH, FONT_SIZE) if (CAPTION and FONT_PATH) else None
    except Exception:
        log.warning("Failed to load font at %s", FONT_PATH)
        return None

FONT = ensure_font()

def caption_image(img: Image.Image, text: str) -> Image.Image:
    if not CAPTION or not text or not FONT:
        return img
    draw = ImageDraw.Draw(img)
    w, h = img.size
    margin = int(FONT_SIZE * 0.6)
    x, y = margin, h - FONT_SIZE - margin
    if CAPTION_SHADOW:
        draw.text((x+2, y+2), text, font=FONT, fill=(0, 0, 0))
    draw.text((x, y), text, font=FONT, fill=(255, 255, 255))
    return img

def fit_long_edge(img: Image.Image, long_edge: int) -> Image.Image:
    if not long_edge or long_edge <= 0:
        return img
    w, h = img.size
    le = max(w, h)
    if le <= long_edge:
        return img
    scale = long_edge / float(le)
    new_size = (int(w*scale), int(h*scale))
    return img.resize(new_size, Image.LANCZOS)

def load_local(path: str) -> bytes:
    with Image.open(path) as im:
        im = fit_long_edge(im.convert("RGB"), LONG_EDGE)
        dt = exif_datetime(path)
        cap = CAPTION_TEXT.format(datetime=dt or "", filename=os.path.basename(path))
        im = caption_image(im, cap)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=JPEG_Q, optimize=True)
        return buf.getvalue()

# For simplicity, for WebDAV/S3 we first cache the original locally then process via PIL.
def cache_original(item: MediaItem) -> str:
    cache_orig = os.path.join(CACHE_DIR, f"{item.id}.orig")
    if os.path.exists(cache_orig):
        return cache_orig

    if item.source == "local":
        return item.path

    if item.source == "webdav":
        assert WebDAVClient, "webdavclient3 not installed"
        wcfg = next(s for s in CFG["sources"] if s["type"] == "webdav")
        client = WebDAVClient({"webdav_hostname": wcfg["url"],
                               "webdav_login": wcfg["username"],
                               "webdav_password": wcfg["password"]})
        client.download_sync(remote_path=item.path, local_path=cache_orig)
        return cache_orig

    if item.source == "s3":
        assert boto3, "boto3 not installed"
        scfg = next(s for s in CFG["sources"] if s["type"] == "s3")
        s3 = boto3.client("s3",
                          endpoint_url=scfg.get("endpoint_url"),
                          aws_access_key_id=scfg.get("access_key"),
                          aws_secret_access_key=scfg.get("secret_key"))
        with open(cache_orig, "wb") as f:
            s3.download_fileobj(scfg["bucket"], item.path, f)
        return cache_orig

    raise RuntimeError("Unknown source")

def render_cached(item: MediaItem) -> str:
    out_jpg = os.path.join(CACHE_DIR, f"{item.id}.jpg")
    if os.path.exists(out_jpg):
        return out_jpg
    src = cache_original(item)
    try:
        with Image.open(src) as im:
            im = fit_long_edge(im.convert("RGB"), LONG_EDGE)
            dt = exif_datetime(src) if os.path.exists(src) else None
            cap = CAPTION_TEXT.format(datetime=dt or "", filename=item.filename)
            im = caption_image(im, cap)
            im.save(out_jpg, "JPEG", quality=JPEG_Q, optimize=True)
    except UnidentifiedImageError:
        log.warning("Skipping unreadable image: %s", item.path)
        raise
    return out_jpg

def matches_any(name: str, globs: List[str]) -> bool:
    return any(fnmatch.fnmatch(name.lower(), g.lower()) for g in globs)

def add_local_source(scfg) -> List[MediaItem]:
    items = []
    globs = scfg.get("include_globs", ["**/*.jpg","**/*.jpeg","**/*.png","**/*.heic"])
    for g in globs:
        for p in glob.glob(os.path.join(scfg["path"], g), recursive=True):
            try:
                st = os.stat(p)
            except FileNotFoundError:
                continue
            items.append(MediaItem(
                id=hash_id("local", p),
                source="local",
                path=p,
                mtime=st.st_mtime,
                size=st.st_size,
                filename=os.path.basename(p)
            ))
    return items

def add_webdav_source(scfg) -> List[MediaItem]:
    if not WebDAVClient:
        log.error("WebDAV requested but webdavclient3 missing")
        return []
    # We’ll list recursively by walking known paths (simple & reliable).
    items = []
    client = WebDAVClient({"webdav_hostname": scfg["url"],
                           "webdav_login": scfg["username"],
                           "webdav_password": scfg["password"]})
    base = "/"
    stack = [base]
    include_globs = scfg.get("include_globs", ["**/*.jpg","**/*.jpeg","**/*.png"])
    # NOTE: Some servers don’t expose recursive listings well; adjust for your tree.
    for root, dirs, files in client.list_iter(base, get_info=True):
        for f in files:
            remote = f["path"]
            name = os.path.basename(remote)
            if not matches_any(remote, include_globs):
                continue
            items.append(MediaItem(
                id=hash_id("webdav", remote),
                source="webdav",
                path=remote,
                mtime=f.get("modified", time.time()),
                size=f.get("size", 0),
                filename=name
            ))
    return items

def add_s3_source(scfg) -> List[MediaItem]:
    if not boto3:
        log.error("S3 requested but boto3 missing")
        return []
    items = []
    s3 = boto3.client("s3",
                      endpoint_url=cfgval(scfg,"endpoint_url"),
                      aws_access_key_id=cfgval(scfg,"access_key"),
                      aws_secret_access_key=cfgval(scfg,"secret_key"))
    paginator = s3.get_paginator('list_objects_v2')
    prefix = scfg.get("prefix","")
    for page in paginator.paginate(Bucket=scfg["bucket"], Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not matches_any(key, scfg.get("include_globs", ["**/*.jpg","**/*.jpeg","**/*.png"])):
                continue
            items.append(MediaItem(
                id=hash_id("s3", key),
                source="s3",
                path=key,
                mtime=obj["LastModified"].timestamp(),
                size=obj["Size"],
                filename=os.path.basename(key)
            ))
    return items

def cfgval(d,k,default=None):
    v=d.get(k,os.environ.get(k.upper(),default))
    return v

def build_playlist():
    global PLAYLIST, PLAYHEAD
    items: List[MediaItem] = []
    min_w, min_h = CFG["playlist"].get("min_resolution", [0,0])
    sources = CFG.get("sources",[])
    for s in sources:
        t = s["type"]
        if t == "local":
            items += add_local_source(s)
        elif t == "webdav":
            items += add_webdav_source(s)
        elif t == "s3":
            items += add_s3_source(s)
    max_age_days = CFG["playlist"].get("max_age_days", 36500)
    cutoff = time.time() - max_age_days*86400
    items = [i for i in items if i.mtime >= cutoff]

    # Optionally sort
    if CFG["playlist"].get("shuffle", True):
        import random
        random.shuffle(items)
    else:
        sort_key = CFG["playlist"].get("sort","mtime")
        items.sort(key=lambda i: (i.mtime if sort_key=="mtime" else i.filename))

    PLAYLIST = items
    PLAYHEAD = 0
    log.info("Playlist ready: %d items", len(PLAYLIST))

# -------- HTTP server ----------
@app.route("/api/reindex", methods=["POST"])
def api_reindex():
    build_playlist()
    return jsonify({"ok": True, "count": len(PLAYLIST)})

@app.route("/api/status")
def api_status():
    return jsonify({
        "count": len(PLAYLIST),
        "playhead": PLAYHEAD,
        "devices": CFG["cast"]["devices"],
        "slide_seconds": CFG["cast"]["slide_seconds"]
    })

@app.route("/image/<img_id>.jpg")
def get_image(img_id):
    # find item
    matches = [m for m in PLAYLIST if m.id == img_id]
    if not matches:
        abort(404)
    item = matches[0]
    try:
        out_path = render_cached(item)
    except Exception:
        abort(500)
    return send_file(out_path, mimetype="image/jpeg", max_age=3600)

def cast_loop(dev_name: str, stop_evt: threading.Event):
    slide_seconds = CFG["cast"]["slide_seconds"]
    global PLAYHEAD
    chromecasts, _ = pychromecast.get_listed_chromecasts(friendly_names=[dev_name])
    if not chromecasts:
        log.error("Chromecast not found: %s", dev_name)
        return
    cast = chromecasts[0]
    cast.wait()
    mc = cast.media_controller

    while not stop_evt.is_set() and PLAYLIST:
        item = PLAYLIST[PLAYHEAD % len(PLAYLIST)]
        url = f"{BASE_URL}/image/{item.id}.jpg"
        log.debug("Casting to %s: %s", dev_name, url)
        mc.play_media(url, "image/jpeg")
        mc.block_until_active(timeout=10)
        # Default Media Receiver shows the image and stays on it.
        # We sleep the slide interval then move on.
        for _ in range(int(slide_seconds*10)):
            if stop_evt.is_set():
                break
            time.sleep(0.1)
        PLAYHEAD += 1

    mc.stop()
    cast.quit_app()
    log.info("Casting stopped for %s", dev_name)

@app.route("/api/start", methods=["POST"])
def api_start():
    # optionally accept {"devices": [...], "shuffle": true, "slide_seconds": 12}
    body = request.get_json(silent=True) or {}
    if "shuffle" in body:
        CFG["playlist"]["shuffle"] = bool(body["shuffle"])
        build_playlist()
    if "slide_seconds" in body:
        CFG["cast"]["slide_seconds"] = int(body["slide_seconds"])
    devices = body.get("devices", CFG["cast"]["devices"])

    # Stop any existing loops
    for dev, evt in list(CAST_STOP_FLAGS.items()):
        evt.set()
    time.sleep(0.5)
    CAST_STOP_FLAGS.clear()
    CAST_THREADS.clear()

    for dev in devices:
        evt = threading.Event()
        t = threading.Thread(target=cast_loop, args=(dev, evt), daemon=True)
        CAST_STOP_FLAGS[dev] = evt
        CAST_THREADS[dev] = t
        t.start()

    return jsonify({"ok": True, "devices": devices})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    for dev, evt in list(CAST_STOP_FLAGS.items()):
        evt.set()
    return jsonify({"ok": True})

if __name__ == "__main__":
    build_playlist()
    host = CFG["server"]["host"]
    port = int(CFG["server"]["port"])
    app.run(host=host, port=port)