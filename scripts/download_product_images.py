#!/usr/bin/env python3
"""
Download product images that still point to external URLs.

Fetches all product_images rows where:
  - external_path is an http(s) URL
  - local_path is NULL or empty

Saves images as WebP to /opt/uniforma/storage/uploads/products/{filename}.webp
and updates the local_path column in the database.

Usage:
    python scripts/download_product_images.py [--dry-run] [--workers N]
"""

import argparse
import asyncio
import io
import os
import sys
from pathlib import Path

import httpx
from PIL import Image
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "")
STORAGE_ROOT = Path("/opt/uniforma/storage/uploads/products")
MAX_SIZE = (1600, 1600)
WEBP_QUALITY = 82
TIMEOUT = 10


def _build_output_path(external_path: str, image_id: int) -> Path:
    """Derive a filename from the URL, falling back to the image id."""
    name = Path(external_path.rstrip("/").split("?")[0]).stem or str(image_id)
    # Sanitize
    name = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return STORAGE_ROOT / f"{name}.webp"


def _convert_to_webp(raw: bytes) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail(MAX_SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=WEBP_QUALITY)
    return buf.getvalue()


async def _download(client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        r = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        return r.content
    except Exception as exc:
        print(f"  FAIL  {url}: {exc}", file=sys.stderr)
        return None


async def run(dry_run: bool, workers: int) -> None:
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set", file=sys.stderr)
        sys.exit(1)

    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, external_path
                FROM product_images
                WHERE external_path ILIKE 'http%'
                  AND (local_path IS NULL OR local_path = '')
                ORDER BY id
                """
            )
        )
        rows = result.fetchall()

    total = len(rows)
    print(f"Found {total} images to download")
    if total == 0 or dry_run:
        if dry_run:
            for row in rows:
                print(f"  DRY  id={row.id}  {row.external_path}")
        return

    sem = asyncio.Semaphore(workers)
    ok = failed = skipped = 0

    async def process(row) -> None:
        nonlocal ok, failed, skipped
        out_path = _build_output_path(row.external_path, row.id)

        if out_path.exists():
            local = f"/uploads/products/{out_path.name}"
            async with async_session() as session:
                await session.execute(
                    text("UPDATE product_images SET local_path = :lp WHERE id = :id"),
                    {"lp": local, "id": row.id},
                )
                await session.commit()
            skipped += 1
            return

        async with sem:
            async with httpx.AsyncClient() as client:
                raw = await _download(client, row.external_path)

        if raw is None:
            failed += 1
            return

        try:
            webp = await asyncio.to_thread(_convert_to_webp, raw)
        except Exception as exc:
            print(f"  CONV  id={row.id}: {exc}", file=sys.stderr)
            failed += 1
            return

        out_path.write_bytes(webp)
        local = f"/uploads/products/{out_path.name}"

        async with async_session() as session:
            await session.execute(
                text("UPDATE product_images SET local_path = :lp WHERE id = :id"),
                {"lp": local, "id": row.id},
            )
            await session.commit()

        print(f"  OK    id={row.id} → {local}")
        ok += 1

    await asyncio.gather(*[process(row) for row in rows])
    await engine.dispose()

    print(f"\nDone: {ok} downloaded, {skipped} already local, {failed} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download product images to local storage")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be downloaded without doing it")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent download workers (default: 8)")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run, workers=args.workers))
