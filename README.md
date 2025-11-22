PhotoCastD — Nextcloud → Chromecast Photo Slideshow Service

PhotoCastD is a lightweight Python service that runs on a Raspberry Pi and turns your Nextcloud photo folders (or any local/S3/WebDAV source) into a Google Photos–style TV slideshow using Chromecast.

It’s designed for home labs and self-hosted setups: minimal dependencies, fast local image serving, zero external APIs.

⸻

✨ Features
	•	Pull photos from:
	•	Local Nextcloud data folders
	•	Nextcloud WebDAV
	•	Wasabi S3 (or any s3-compatible backend)
	•	Automatic playlist building with:
	•	Shuffle or ordered
	•	Min resolution filters
	•	Max age filters
	•	Recursive folder scan
	•	Optimized image rendering:
	•	Resize to TV-friendly long edge
	•	HEIC support (pillow-heif)
	•	Optional EXIF timestamp + filename caption
	•	Chromecast slideshow:
	•	Works with Default Media Receiver
	•	Multiple devices at once
	•	Configurable slide interval
	•	REST API for remote control:
	•	/api/start
	•	/api/stop
	•	/api/reindex
	•	/api/status
	•	Systemd service for auto-start on boot
	•	Fully configurable via config.yaml

⸻

🧱 Project Structure

photocastd/
 ├── app.py             # main service
 ├── config.yaml        # Slideshow + source configuration
 ├── requirements.txt   # Python dependencies
 ├── service.sh         # Installer + systemd setup script
 ├── README.md          # this file


 🚀 Installation on Raspberry Pi

1. Copy or clone the repository

cd /opt
sudo git clone https://github.com/<YOUR-USERNAME>/photocastd.git
sudo chown -R pi:pi photocastd
cd photocastd

2. Run the installer

chmod +x service.sh
./service.sh

This will:
	•	create a Python venv
	•	install dependencies
	•	create and enable a photocastd.service systemd unit
	•	start the service automatically

3. Check status

sudo systemctl status photocastd
sudo journalctl -u photocastd -f

⚙️ Configuration (config.yaml)

The service is fully configured through config.yaml.

📡 REST API

start slideshow
curl -X POST http://raspi.local:8099/api/start

stop
curl -X POST http://raspi.local:8099/api/stop

Reindex image sources
curl -X POST http://raspi.local:8099/api/reindex

Status
curl http://raspi.local:8099/api/status

🖥 Development Flow (Mac → Pi)

Typical workflow:

On Mac:
~/MyApps/photocastd
# edit code in Rider
git add .
git commit -m "Some change"
git push
On Pi:

cd /opt/photocastd
git pull
sudo systemctl restart photocastd
sudo journalctl -u photocastd -n 50 -f

🧪 Testing locally

python3 app.py
curl http://localhost:8099/api/status

🛠 Troubleshooting

sudo journalctl -u photocastd -n 100 --no-pager
