from __future__ import annotations

from app.schemas.sync import PimSyncResponse


def summarize_stock_sync(result: PimSyncResponse) -> dict[str, int]:
    return {
        "variants_created": result.variants_created,
        "variants_updated": result.variants_updated,
        "products_created": result.products_created,
        "products_updated": result.products_updated,
    }
