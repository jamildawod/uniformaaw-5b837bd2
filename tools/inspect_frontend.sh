#!/usr/bin/env bash
set -euo pipefail

FRONTEND_PATH="${1:-/opt/uniforma/frontend}"

if [ ! -d "$FRONTEND_PATH" ]; then
  echo "Frontend saknas: $FRONTEND_PATH"
  exit 1
fi

echo "=== FRONTEND INSPEKTION ==="
echo "Path: $FRONTEND_PATH"

echo
echo "Filer:"
find "$FRONTEND_PATH" -maxdepth 2

echo
echo "package.json:"
cat "$FRONTEND_PATH/package.json" 2>/dev/null || echo "saknas"

echo
echo "API calls:"
grep -R "fetch\|axios" "$FRONTEND_PATH" 2>/dev/null | head -20 || true

echo
echo "Next/Vite:"
grep -R "next\|vite" "$FRONTEND_PATH" 2>/dev/null | head -20 || true
