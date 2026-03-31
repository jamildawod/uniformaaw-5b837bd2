#!/usr/bin/env bash
# backup_images.sh — Datumstämplad backup av /opt/uniforma/storage/images
#
# Användning:
#   ./scripts/backup_images.sh                  # backup till default-katalog
#   ./scripts/backup_images.sh /mnt/backups      # backup till valfri sökväg
#
# Cron-exempel (nattlig backup 03:00):
#   0 3 * * * /opt/uniforma/scripts/backup_images.sh /opt/uniforma/backups >> /var/log/uniforma-backup.log 2>&1

set -euo pipefail

SOURCE_DIR="/opt/uniforma/storage/images"
BACKUP_ROOT="${1:-/opt/uniforma/backups/images}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST="${BACKUP_ROOT}/${TIMESTAMP}"
KEEP_DAYS="${KEEP_DAYS:-30}"  # antal dagar att behålla backuper

echo "[$(date -Iseconds)] backup_images: start"
echo "  källa  : ${SOURCE_DIR}"
echo "  mål    : ${DEST}"

# Skapa målkatalog
mkdir -p "${DEST}"

# Kopiera med hårdlänkar för att spara disk (rsync --link-dest)
LATEST_LINK="${BACKUP_ROOT}/latest"

if [ -d "${LATEST_LINK}" ]; then
  rsync -a --link-dest="${LATEST_LINK}" "${SOURCE_DIR}/" "${DEST}/"
else
  rsync -a "${SOURCE_DIR}/" "${DEST}/"
fi

# Uppdatera symlink till senaste backup
ln -sfn "${DEST}" "${LATEST_LINK}"

# Statistik
FILE_COUNT="$(find "${DEST}" -type f | wc -l)"
DEST_SIZE="$(du -sh "${DEST}" | cut -f1)"
echo "  filer  : ${FILE_COUNT}"
echo "  storlek: ${DEST_SIZE}"

# Rensa backuper äldre än KEEP_DAYS dagar
REMOVED=0
while IFS= read -r old_backup; do
  rm -rf "${old_backup}"
  REMOVED=$((REMOVED + 1))
done < <(find "${BACKUP_ROOT}" -maxdepth 1 -mindepth 1 -type d \
           -name "20*" \
           -mtime "+${KEEP_DAYS}" 2>/dev/null)

[ "${REMOVED}" -gt 0 ] && echo "  rensat : ${REMOVED} gamla backuper (>${KEEP_DAYS} dagar)"

echo "[$(date -Iseconds)] backup_images: klar"
