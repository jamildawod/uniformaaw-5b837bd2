#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.size import normalize_size
from app.db.session import get_session_factory
from app.models.product_variant import ProductVariant


def _variant_key(variant: ProductVariant) -> tuple[str, str | None, str | None]:
    color = variant.color.lower() if variant.color else None
    return (str(variant.product_id), color, variant.size)


def _pick_keeper(left: ProductVariant, right: ProductVariant) -> ProductVariant:
    left_score = (
        1 if left.deleted_at is None else 0,
        1 if left.is_active else 0,
        left.stock_quantity or 0,
        -(left.id or 0),
    )
    right_score = (
        1 if right.deleted_at is None else 0,
        1 if right.is_active else 0,
        right.stock_quantity or 0,
        -(right.id or 0),
    )
    return left if left_score >= right_score else right


async def main() -> None:
    session_factory = get_session_factory()

    async with session_factory() as session:
        result = await session.execute(
            select(ProductVariant).options(selectinload(ProductVariant.images))
        )
        variants = list(result.scalars().all())

        deleted_invalid = 0
        deleted_duplicates = 0
        normalized_count = 0
        merged_count = 0
        grouped: dict[tuple[str, str | None, str | None], ProductVariant] = {}

        for variant in variants:
            normalized_size = normalize_size(variant.size)
            if normalized_size is None:
                await session.delete(variant)
                deleted_invalid += 1
                continue

            if variant.size != normalized_size:
                variant.size = normalized_size
                normalized_count += 1

            key = _variant_key(variant)
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = variant
                continue

            keeper = _pick_keeper(existing, variant)
            duplicate = variant if keeper is existing else existing
            grouped[key] = keeper

            keeper.is_active = keeper.is_active or duplicate.is_active
            keeper.stock_quantity = max(keeper.stock_quantity or 0, duplicate.stock_quantity or 0)
            keeper.deleted_at = None if keeper.deleted_at is None or duplicate.deleted_at is None else keeper.deleted_at

            keeper_paths = {image.external_path for image in keeper.images}
            for image in duplicate.images:
                if image.external_path in keeper_paths:
                    continue
                image.variant_id = keeper.id
                keeper_paths.add(image.external_path)

            await session.delete(duplicate)
            deleted_duplicates += 1
            merged_count += 1

        await session.commit()

        print(
            {
                "normalized": normalized_count,
                "deleted_invalid": deleted_invalid,
                "deleted_duplicates": deleted_duplicates,
                "merged_duplicates": merged_count,
            }
        )


if __name__ == "__main__":
    asyncio.run(main())
