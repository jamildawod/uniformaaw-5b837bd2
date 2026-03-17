from __future__ import annotations

from app.services.pim_ingestion_service import ProductPayload


def count_image_matches(grouped_products: dict[str, ProductPayload]) -> int:
    return sum(len(product.image_paths) for product in grouped_products.values())
