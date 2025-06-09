#!/bin/bash

set -e

echo "=== Tworzenie venv ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Instalacja zależności ==="
pip install -r requirements.txt

echo "=== Kopiowanie service do systemd ==="
sudo cp webhook.service /etc/systemd/system/webhook.service

echo "=== Reload systemd ==="
sudo systemctl daemon-reload

echo "=== Enable i start webhook.service ==="
sudo systemctl enable webhook.service
sudo systemctl restart webhook.service

echo "=== Status webhook.service ==="
sudo systemctl status webhook.service

echo "=== GOTOWE ==="
