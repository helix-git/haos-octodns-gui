#!/bin/bash
# Lokale Entwicklungsumgebung starten

set -e

# Virtuelle Umgebung erstellen falls nicht vorhanden
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt
else
    source venv/bin/activate
fi

# Umgebungsvariablen für lokale Entwicklung
export ZONE_FILE_PATH="${ZONE_FILE_PATH:-./zones}"
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN:-dev-token}"

# Zone-Verzeichnis erstellen
mkdir -p "$ZONE_FILE_PATH"

echo "Starting OctoDNS GUI in development mode..."
echo "Zone file path: $ZONE_FILE_PATH"
echo "Open http://localhost:8100 in your browser"
echo ""

# Flask starten
cd app
python app.py
