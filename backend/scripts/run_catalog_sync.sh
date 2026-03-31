#!/usr/bin/env bash
set -euo pipefail

cd /opt/uniforma

echo "Running supplier sync"
docker compose exec -T backend python3 backend/scripts/run_catalog_sync.py
