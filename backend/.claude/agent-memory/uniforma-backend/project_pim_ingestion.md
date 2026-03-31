---
name: PIM ingestion pipeline architecture and known quirks
description: PimIngestionService CSV format, Docker execution, known column mapping issues, advisory lock behavior
type: project
---

## CSV Format (actual PIM export)

- Location: `/opt/uniforma/data/PIMexport_catalog_sv-SE.csv`
- Delimiter: `;` (semicolon)
- Fields are double-quoted, so semicolons inside fields (Images, Sizes) parse correctly
- **One row per color variant** — `ItemNo` like `102001-541` includes the color suffix
- `Sizes` field: semicolon-delimited list of sizes for that color (e.g. `"2XS;XS;S;M;L;XL;2XL;3XL"`) — the service reads only the first token via `normalize_size`
- `Images` field: semicolon-delimited list of image URLs — needs `;` splitting in `_get_image_paths`
- `EANCodes` field: semicolon-delimited list of EANs for all sizes — too long for `VARCHAR(64)`, do NOT map to `ean`
- 1912 of 2251 rows have empty `Sizes` — these correctly produce no variants (skipped)
- ~339 rows with valid sizes produce variants

## Column mapping added to `_build_resolver`

Added to `pim_ingestion_service.py`:
- `name`: `ENSOName`, `AdditionalName`
- `description`: `ENSODescription`, `AdditionalDescription`, `ENSOWebText`, `AdditionalWebText`
- `sku`: `ItemNo`
- `color`: `ColorNames`
- `size`: `Sizes`
- `_get_image_paths`: now splits on `;` in addition to `|` and `,`

## Docker execution

- App code is baked into the Docker image (not volume-mounted) — host edits require `docker cp` or image rebuild
- Only `/opt/uniforma/storage` and `/opt/uniforma/data` are bind-mounted
- `WORKDIR` inside container is `/app`
- Run sync: `docker exec uniforma-api python3 -m backend.scripts.run_catalog_sync`
- Or from host: `docker compose exec backend python3 -m backend.scripts.run_catalog_sync`

## Advisory lock

- `PimSyncService` uses PostgreSQL advisory lock (session-scoped)
- Stale lock after crashed run: find with `SELECT pid, classid, objid FROM pg_locks WHERE locktype = 'advisory'`
- Release by terminating: `SELECT pg_terminate_backend(<pid>)`
- `pg_advisory_unlock_all()` only works within the same session — useless from psql

## Entrypoint

- `/opt/uniforma/backend/scripts/run_catalog_sync.py` — clean async entrypoint
- Requires `/opt/uniforma/backend/__init__.py` and `/opt/uniforma/backend/scripts/__init__.py`
- Command: `python -m backend.scripts.run_catalog_sync` (from `/app` inside container)
