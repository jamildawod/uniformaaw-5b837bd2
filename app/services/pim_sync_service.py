import hashlib
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.models.ingestion_log import IngestionLog
from app.models.sync_run import SyncRun
from app.repositories.product_repository import ProductRepository
from app.schemas.sync import PimSyncResponse
from app.services.cache_service import CacheService
from app.services.ftp_image_service import FtpImageService
from app.services.image_service import ImageService
from app.services.pim_ingestion_service import PimIngestionService
from app.services.product_read_service import ProductReadService


class PimSyncService:
    def __init__(
        self,
        ingestion_service: PimIngestionService,
        image_service: FtpImageService,
        settings: Settings,
        cache_service: CacheService | None = None,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.image_service = image_service
        self.settings = settings
        self.cache_service = cache_service
        self.logger = get_logger(self.__class__.__name__)

    async def run_sync(self) -> PimSyncResponse:
        session = self.ingestion_service.session
        lock_acquired = False
        supplier = await self.ingestion_service.get_or_create_default_supplier()
        sync_run = SyncRun(
            supplier_id=supplier.id,
            started_at=datetime.now(UTC),
            status="running",
        )
        ingestion_log = IngestionLog(
            supplier_id=supplier.id,
            started_at=sync_run.started_at,
            status="running",
        )
        session.add(sync_run)
        session.add(ingestion_log)
        await session.flush()
        ingestion_log.sync_run_id = sync_run.id
        await session.commit()
        advisory_lock_key = self._advisory_lock_key()

        try:
            self.logger.info("Attempting to acquire PIM sync advisory lock.")
            result = await session.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": advisory_lock_key},
            )
            lock_acquired = bool(result.scalar())
            if not lock_acquired:
                self.logger.warning("PIM sync advisory lock is already held.")
                await self._finalize_run(
                    session,
                    sync_run,
                    ingestion_log,
                    status_value="failed",
                    error_message="Sync already running",
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Sync already running",
                )
            self.logger.info("PIM sync advisory lock acquired.")

            sync_result = await self.ingestion_service.ingest()
            sync_result.images_synced = await self.image_service.sync_images()
            await self._finalize_run(
                session,
                sync_run,
                ingestion_log,
                status_value="success",
                sync_result=sync_result,
            )
            if self.cache_service is not None:
                await self.cache_service.delete(ProductReadService.FILTERS_CACHE_KEY)
            self.logger.info("PIM sync finished with result: %s", sync_result.model_dump())
            return sync_result
        except IntegrityError as exc:
            await session.rollback()
            await self._finalize_run(
                session,
                sync_run,
                ingestion_log,
                status_value="failed",
                error_message=str(exc),
            )
            self.logger.error(
                "PIM sync integrity error",
                extra={
                    "event": "pim_sync_integrity_error",
                    "error": str(exc),
                },
            )
            raise
        except Exception as exc:
            await session.rollback()
            await self._finalize_run(
                session,
                sync_run,
                ingestion_log,
                status_value="failed",
                error_message=str(exc),
            )
            self.logger.error(
                "PIM sync failed",
                extra={
                    "event": "pim_sync_failed",
                    "error": str(exc),
                },
            )
            raise
        finally:
            if lock_acquired:
                self.logger.info("Releasing PIM sync advisory lock.")
                await session.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": advisory_lock_key},
                )
                await session.commit()

    async def _finalize_run(
        self,
        session: AsyncSession,
        sync_run: SyncRun,
        ingestion_log: IngestionLog,
        status_value: str,
        sync_result: PimSyncResponse | None = None,
        error_message: str | None = None,
    ) -> None:
        finished_at = datetime.now(UTC)
        sync_run.finished_at = finished_at
        sync_run.status = status_value
        sync_run.error_message = error_message
        ingestion_log.finished_at = finished_at
        ingestion_log.status = status_value
        ingestion_log.error_message = error_message

        if sync_result is not None:
            sync_run.products_created = sync_result.products_created
            sync_run.products_updated = sync_result.products_updated
            sync_run.variants_created = sync_result.variants_created
            sync_run.variants_updated = sync_result.variants_updated
            sync_run.images_synced = sync_result.images_synced
            sync_run.rows_processed = sync_result.rows_processed
            sync_run.rows_created = sync_result.rows_created
            sync_run.rows_updated = sync_result.rows_updated
            sync_run.rows_failed = sync_result.rows_failed

            ingestion_log.rows_processed = sync_result.rows_processed
            ingestion_log.rows_created = sync_result.rows_created
            ingestion_log.rows_updated = sync_result.rows_updated
            ingestion_log.rows_failed = sync_result.rows_failed

        session.add(sync_run)
        session.add(ingestion_log)
        await session.commit()

    def _advisory_lock_key(self) -> int:
        digest = hashlib.sha256(self.settings.project_slug.encode("utf-8")).digest()
        key = int.from_bytes(digest[:8], byteorder="big", signed=False)
        if key >= 2**63:
            key -= 2**64
        return key


def build_pim_sync_service(session: AsyncSession, settings: Settings) -> PimSyncService:
    product_repository = ProductRepository(session)
    image_service = ImageService(settings)
    return PimSyncService(
        PimIngestionService(session, product_repository, settings, image_service=image_service),
        FtpImageService(session, product_repository, settings, image_service),
        settings,
        cache_service=CacheService(settings),
    )
