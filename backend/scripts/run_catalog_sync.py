"""CLI entrypoint: run the PIM catalog ingestion sync.

Usage inside the Docker container (from /app):

    python -m backend.scripts.run_catalog_sync

Or directly:

    python backend/scripts/run_catalog_sync.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Ensure /app (the repo root inside the container) is on sys.path so that
# both `app.*` and `backend.*` packages resolve correctly regardless of cwd.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402
from app.db.session import dispose_engine, get_session_factory  # noqa: E402
from app.services.pim_sync_service import build_pim_sync_service  # noqa: E402

logger = logging.getLogger("run_catalog_sync")


async def main() -> None:
    configure_logging()
    settings = get_settings()

    logger.info(
        "Starting PIM catalog sync | csv=%s batch_size=%d",
        settings.pim_csv_path,
        settings.pim_batch_size,
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        sync_service = build_pim_sync_service(session, settings)

        # Resolve and log the CSV path before starting so any FileNotFoundError
        # is surfaced early with a clear message.
        try:
            source_path = sync_service.ingestion_service.resolve_source_csv_path()
            logger.info("CSV source resolved: %s", source_path)
        except FileNotFoundError as exc:
            logger.error("CSV file not found: %s", exc)
            sys.exit(1)

        result = await sync_service.run_sync()

    await dispose_engine()

    logger.info(
        "PIM sync completed | products_created=%d products_updated=%d products_unchanged=%d "
        "variants_created=%d variants_updated=%d variants_unchanged=%d "
        "images_discovered=%d images_synced=%d "
        "rows_processed=%d rows_failed=%d",
        result.products_created,
        result.products_updated,
        result.products_unchanged,
        result.variants_created,
        result.variants_updated,
        result.variants_unchanged,
        result.images_discovered,
        result.images_synced,
        result.rows_processed,
        result.rows_failed,
    )

    # Also emit as JSON for easy machine consumption / log scraping.
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
