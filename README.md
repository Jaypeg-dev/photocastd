# photocastd — Chromecast Photo Slideshow

Automated photo casting to Chromecast devices from local or Nextcloud sources.

## Features

- 📸 Cast photos from local directories to Chromecast devices
- 🔄 Automatic slideshow with configurable intervals
- 📂 Multiple image sources (local, Nextcloud)
- ⚙️ Per-device source routing (device → default source)
- 🎯 Runtime source override via API
- 🚀 Zero external dependencies (uses pychromecast)

## Quick Start

### Install

```bash
pip install -r requirements.txt
```

### Configure

Create `config.yaml`:

```yaml
# Where images come from. Prefer local Nextcloud data folders for speed.
sources:
  - type: local
    path: /media/Pictures/Favs
    include_globs: ["**/*.jpg", "**/*.jpeg", "**/*.png", "**/*.heic"]

playlist:
  shuffle: true
  recursive: true
  min_resolution: [1280, 720]
  max_age_days: 36500
  sort: "mtime"

render:
  long_edge: 1920
  jpeg_quality: 88
  heic_support: true
  # Display mode for portrait images on 16:9 TV:
  # - letterbox: keep aspect ratio, add black bars (default, safe)
  # - resize: stretch to fill 16:9 (may distort portrait images)
  # - side-by-side: tile 2 portrait photos horizontally (recommended for 9:16 Pinterest photos)
  display_mode: side-by-side
  tv_width: 1920
  tv_height: 1080
  caption:
    enabled: true
    text: "{datetime}  ·  {filename}"
    font_path: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_size: 28
    shadow: true

cast:
  devices:
    - "SalleTV"
    - "Gym"
    - "KitchenNest"
  slide_seconds: 15
  preload_next: true

server:
  host: "::"
  port: 8099
  base_url: "http://192.168.20.56:8099"

logging:
  level: INFO
  file: "/var/log/photocastd.log"
```

### Run

```bash
python app.py
```

Server listens on `http://0.0.0.0:8099`

---

## API

### Start slideshow on device

**Endpoint:** `POST /api/start_device`

**Parameters:**
- `device` (string, required) — Device name from config (e.g., `Gym`, `Kitchen`)
- `source` (string, optional) — Override default source path. If omitted, uses device's default from `routing.device_sources`
- `slide_seconds` (integer, optional) — Duration to display each image (seconds). If omitted, uses default from `cast.slide_seconds` config
- `shuffle` (boolean, optional) — Randomize playlist order. If omitted, uses default from `playlist.shuffle` config

**Examples:**

*With device's default source:*
```bash
curl -X POST http://raspi.local:8099/api/start_device \
  -H "Content-Type: application/json" \
  -d '{"device": "Gym"}'
```

*With custom source override:*
```bash
curl -X POST http://raspi.local:8099/api/start_device \
  -H "Content-Type: application/json" \
  -d '{"device": "Gym", "source": "/media/Pictures/2026"}'
```

*With custom slide timing and shuffle:*
```bash
curl -X POST http://raspi.local:8099/api/start_device \
  -H "Content-Type: application/json" \
  -d '{"device": "Kitchen", "slide_seconds": 15, "shuffle": true}'
```

*Full example with all parameters:*
```bash
curl -X POST http://raspi.local:8099/api/start_device \
  -H "Content-Type: application/json" \
  -d '{"device": "Gym", "source": "/media/Pictures/2026", "slide_seconds": 20, "shuffle": false}'
```

**Response:**
```json
{"ok": true, "device": "Gym", "status": "started"}
```

If the device is already running and no source change is requested, the response is:
```json
{"ok": true, "device": "Gym", "status": "already_running"}
```

---

### Stop slideshow on device

**Endpoint:** `POST /api/stop_device`

**Parameters:**
- `device` (string, required) — Device name

**Example:**
```bash
curl -X POST http://raspi.local:8099/api/stop_device \
  -H "Content-Type: application/json" \
  -d '{"device": "Gym"}'
```

---

### Health check

**Endpoint:** `GET /health`

**Response:**
```json
{"status": "ok", "devices": ["Gym", "Kitchen", "Bedroom"]}
```

---

## Systemd Service

Install as systemd service:

```bash
sudo cp photocastd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable photocastd
sudo systemctl start photocastd
```

Check status:
```bash
sudo systemctl status photocastd
sudo journalctl -u photocastd -f
```

---

## Troubleshooting

```bash
sudo journalctl -u photocastd -n 100 --no-pager
```
