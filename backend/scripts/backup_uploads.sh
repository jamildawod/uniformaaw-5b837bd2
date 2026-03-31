#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:-/opt/uniforma/storage/uploads}"
BACKUP_ROOT="${2:-/opt/uniforma/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_DIR="${BACKUP_ROOT}/uploads"
ARCHIVE_PATH="${TARGET_DIR}/uploads-${STAMP}.tar.gz"

mkdir -p "${TARGET_DIR}"
tar -C "${SOURCE_DIR}" -czf "${ARCHIVE_PATH}" .

find "${TARGET_DIR}" -type f -name 'uploads-*.tar.gz' -mtime +14 -delete

echo "Created ${ARCHIVE_PATH}"
