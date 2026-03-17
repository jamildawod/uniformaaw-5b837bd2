#!/usr/bin/env bash
set -euo pipefail

cd /opt/uniforma

echo "Running Hejco sync"
docker compose exec -T backend python3 backend/scripts/run_hejco_sync.py
