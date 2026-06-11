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

# Route devices to sources
routing:
  device_sources:
    Gym: /media/Pictures/GymPics
    Kitchen: /media/Pictures/Favs
    Bedroom: /media/Pictures/2026

# Chromecast devices
cast:
  devices:
    Gym: "Gym Nest Hub"
    Kitchen: "Kitchen Nest Hub"
    Bedroom: "Bedroom Nest Mini"
  
  # Slideshow timing
  interval: 30  # seconds per image
  transition: 2  # fade duration (seconds)
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
