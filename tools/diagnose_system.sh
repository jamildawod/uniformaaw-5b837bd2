#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/opt/uniforma"
REPORTS_DIR="$BASE_DIR/reports"
TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
REPORT="$REPORTS_DIR/system_$TIMESTAMP.txt"

mkdir -p "$REPORTS_DIR"

{
echo "=== SYSTEM DIAGNOS ==="
date

echo
echo "OS:"
uname -a

echo
echo "TOOLS:"
for cmd in git node npm python3 docker; do
  command -v $cmd && echo "$cmd OK" || echo "$cmd saknas"
done

echo
echo "PORTAR:"
command -v lsof >/dev/null && lsof -iTCP -sTCP:LISTEN -P || true

echo
echo "DOCKER:"
docker ps -a || true

echo
echo "STRUKTUR:"
find "$BASE_DIR" -maxdepth 2 -type d

} | tee "$REPORT"

echo "Sparad: $REPORT"
