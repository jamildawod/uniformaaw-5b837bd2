#!/usr/bin/env bash
set -euo pipefail

BACKEND_PATH="${1:-/opt/uniforma/backend}"

if [ ! -d "$BACKEND_PATH" ]; then
  echo "Backend saknas: $BACKEND_PATH"
  exit 1
fi

echo "=== BACKEND INSPEKTION ==="
echo "Path: $BACKEND_PATH"

echo
echo "Filer:"
find "$BACKEND_PATH" -maxdepth 2

echo
echo "Env:"
find "$BACKEND_PATH" -name ".env*"

echo
echo "API kod:"
grep -R "fastapi\|express\|router" "$BACKEND_PATH" 2>/dev/null | head -20 || true

echo
echo "DB:"
grep -R "postgres\|mysql\|sqlite" "$BACKEND_PATH" 2>/dev/null | head -20 || true
