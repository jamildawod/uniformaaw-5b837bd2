import io
import hashlib
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageOps

from app.core.config import Settings
from app.core.logging import get_logger


class ImageService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)

    async def download_http_image(self, url: str) -> str | None:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self.settings.image_download_timeout_seconds,
                headers={"User-Agent": "Uniforma-ImagePipeline/1.0"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except Exception as exc:
            self.logger.warning(
                "HTTP image download failed",
                extra={
                    "event": "image_http_download_failed",
                    "url": url,
                    "error": str(exc),
                },
            )
            return None

        return await self.store_image_bytes(response.content, source_hint=url)

    async def store_image_bytes(self, raw: bytes, source_hint: str) -> str | None:
        try:
            uploads_root = self.settings.product_upload_root
            uploads_root.mkdir(parents=True, exist_ok=True)

            filename = self._build_filename(source_hint)
            destination = uploads_root / filename
            if destination.exists():
                return f"/uploads/products/{filename}"

            with Image.open(io.BytesIO(raw)) as image:
                image = ImageOps.exif_transpose(image)
                if image.mode not in ("RGB", "RGBA"):
                    image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
                image.thumbnail(
                    (self.settings.image_max_width, self.settings.image_max_height),
                    Image.Resampling.LANCZOS,
                )
                image.save(
                    destination,
                    "WEBP",
                    quality=self.settings.image_webp_quality,
                    method=6,
                    optimize=True,
                )
        except Exception as exc:
            self.logger.warning(
                "Image processing failed",
                extra={
                    "event": "image_processing_failed",
                    "source_hint": source_hint,
                    "error": str(exc),
                },
            )
            return None

        return f"/uploads/products/{filename}"

    def _build_filename(self, source_hint: str) -> str:
        parsed = urlparse(source_hint)
        stem = Path(parsed.path or source_hint).stem or "product-image"
        safe_stem = "".join(ch.lower() if ch.isalnum() else "-" for ch in stem).strip("-")
        safe_stem = safe_stem[:40] or "product-image"
        digest = hashlib.sha256(source_hint.encode("utf-8")).hexdigest()[:16]
        return f"{digest}-{safe_stem}.webp"
