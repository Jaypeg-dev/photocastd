#!/usr/bin/env bash
set -euo pipefail

cd /opt/photocastd
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create systemd unit
sudo tee /etc/systemd/system/photocastd.service >/dev/null <<'UNIT'
[Unit]
Description=PhotoCast Daemon (Nextcloud -> Chromecast)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/photocastd
ExecStart=/opt/photocastd/.venv/bin/python /opt/photocastd/app.py
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now photocastd
sudo systemctl status --no-pager photocastd