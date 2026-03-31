from __future__ import annotations

from app.schemas.sync import PimSyncResponse
from app.services.pim_ingestion_service import PimIngestionService


async def import_products(service: PimIngestionService) -> PimSyncResponse:
    return await service.ingest()
