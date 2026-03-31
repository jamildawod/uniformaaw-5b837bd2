import asyncio
from ftplib import FTP
from pathlib import PurePosixPath

import paramiko
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.repositories.product_repository import ProductRepository
from app.services.image_service import ImageService


class FtpImageService:
    def __init__(
        self,
        session: AsyncSession,
        product_repository: ProductRepository,
        settings: Settings,
        image_service: ImageService,
    ) -> None:
        self.session = session
        self.product_repository = product_repository
        self.settings = settings
        self.image_service = image_service
        self.logger = get_logger(self.__class__.__name__)

    # ── Public API ────────────────────────────────────────────────

    async def sync_images(self) -> int:
        self.settings.product_upload_root.mkdir(parents=True, exist_ok=True)

        ftp_images = await self.product_repository.list_images_needing_sync()
        http_images = await self.product_repository.list_http_images_needing_download()
        ftp_images_by_path = self._group_images_by_external_path(ftp_images)
        http_images_by_path = self._group_images_by_external_path(http_images)

        ftp_configured = bool(
            self.settings.ftp_host
            and self.settings.ftp_username
            and self.settings.ftp_password
        )

        if ftp_images and not ftp_configured:
            self.logger.warning(
                "FTP/SFTP not configured; %s FTP images will not be downloaded",
                len(ftp_images),
            )

        ftp_dl = ftp_failed = 0
        http_dl = http_failed = 0
        updated = 0
        batch_size = 50

        # ── FTP images ──────────────────────────────────────────
        for ep, images in ftp_images_by_path.items():
            if not ep:
                continue
            if not ftp_configured:
                ftp_failed += len(images)
                continue

            try:
                raw = await self._download_ftp_bytes(ep)
            except Exception as exc:
                self.logger.warning("FTP download failed %s: %s", ep, exc)
                ftp_failed += len(images)
                continue

            if raw is None:
                ftp_failed += len(images)
                continue

            saved = await self.image_service.store_image_bytes(raw, ep)
            if saved is None:
                ftp_failed += len(images)
                continue

            for image in images:
                image.local_path = saved
                updated += 1
            ftp_dl += len(images)

            if updated % batch_size == 0:
                await self.session.commit()

        # ── HTTP/HTTPS images ────────────────────────────────────
        for ep, images in http_images_by_path.items():
            if not ep:
                continue

            saved = await self.image_service.download_http_image(ep)
            if saved is None:
                http_failed += len(images)
                continue

            for image in images:
                image.local_path = saved
                updated += 1
            http_dl += len(images)

            if updated % batch_size == 0:
                await self.session.commit()

        if updated:
            await self.session.commit()

        self.logger.info(
            "Image sync: ftp_dl=%s ftp_fail=%s | http_dl=%s http_fail=%s",
            ftp_dl,
            ftp_failed,
            http_dl,
            http_failed,
        )
        return ftp_dl + http_dl

    def _group_images_by_external_path(self, images: list) -> dict[str, list]:
        grouped: dict[str, list] = {}
        for image in images:
            if image.external_path is None:
                continue
            grouped.setdefault(image.external_path, []).append(image)
        return grouped

    # ── Download helpers ──────────────────────────────────────────

    async def _download_ftp_bytes(self, external_path: str) -> bytes | None:
        if not (self.settings.ftp_host and self.settings.ftp_username and self.settings.ftp_password):
            return None
        if self.settings.ftp_protocol == "sftp":
            return await asyncio.to_thread(self._download_via_sftp, external_path)
        return await asyncio.to_thread(self._download_via_ftp, external_path)

    def _download_via_sftp(self, external_path: str) -> bytes:
        transport = paramiko.Transport(
            (self.settings.ftp_host, self.settings.ftp_port or 22)
        )
        transport.connect(
            username=self.settings.ftp_username,
            password=self.settings.ftp_password,
        )
        sftp = paramiko.SFTPClient.from_transport(transport)
        try:
            remote_path = self._ftp_remote_path(external_path)
            with sftp.file(remote_path, "rb") as f:
                return f.read()
        finally:
            sftp.close()
            transport.close()

    def _download_via_ftp(self, external_path: str) -> bytes:
        ftp = FTP()
        ftp.connect(
            host=self.settings.ftp_host,
            port=self.settings.ftp_port or 21,
            timeout=self.settings.ftp_timeout_seconds,
        )
        ftp.login(self.settings.ftp_username, self.settings.ftp_password)
        chunks: list[bytes] = []
        try:
            ftp.retrbinary(f"RETR {self._ftp_remote_path(external_path)}", chunks.append)
            return b"".join(chunks)
        finally:
            ftp.quit()

    # ── Path helpers ──────────────────────────────────────────────

    def _ftp_remote_path(self, external_path: str) -> str:
        base = PurePosixPath(self.settings.ftp_remote_base_path)
        path = PurePosixPath(external_path.lstrip("/"))
        return str(base / path)
