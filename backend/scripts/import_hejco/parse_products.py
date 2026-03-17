from __future__ import annotations

from pathlib import Path

from app.services.pim_ingestion_service import PimIngestionService, ProductPayload


def parse_product_export(service: PimIngestionService, csv_path: Path) -> dict[str, ProductPayload]:
    return service._read_and_group(csv_path)  # noqa: SLF001
