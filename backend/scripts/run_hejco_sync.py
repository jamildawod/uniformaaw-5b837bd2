import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import get_settings
from app.db.session import dispose_engine, get_session_factory
from app.repositories.product_repository import ProductRepository
from app.services.ftp_image_service import FtpImageService
from app.services.pim_ingestion_service import PimIngestionService
from app.services.pim_sync_service import PimSyncService
from backend.scripts.import_hejco.match_images import count_image_matches
from backend.scripts.import_hejco.parse_products import parse_product_export


async def main() -> None:
    settings = get_settings()
    source_path = settings.pim_csv_path
    if not source_path.exists():
        raise FileNotFoundError(f"Hejco source file not found: {source_path}")

    print(f"Hejco sync source is available: {source_path}")
    session_factory = get_session_factory()
    async with session_factory() as session:
        product_repository = ProductRepository(session)
        ingestion_service = PimIngestionService(session, product_repository, settings, supplier_slug="hejco")
        preview = parse_product_export(ingestion_service, source_path)
        print(
            f"Previewed {len(preview)} Hejco products and {count_image_matches(preview)} supplier image references before import."
        )
        sync_service = PimSyncService(
            ingestion_service,
            FtpImageService(session, product_repository, settings),
            settings,
        )
        result = await sync_service.run_sync()
        print(result.model_dump_json())

    await dispose_engine()
    print("Hejco sync entrypoint completed.")


if __name__ == "__main__":
    asyncio.run(main())
