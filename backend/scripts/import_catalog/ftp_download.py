from __future__ import annotations

import asyncio
from ftplib import FTP
from pathlib import Path, PurePosixPath

import paramiko

from app.core.config import Settings


def _remote_path(settings: Settings, remote_name: str) -> str:
    base = PurePosixPath(settings.ftp_remote_base_path)
    return str(base / remote_name.lstrip("/"))


def _download_via_sftp(settings: Settings, remote_name: str) -> bytes:
    transport = paramiko.Transport((settings.ftp_host, settings.ftp_port or 22))
    transport.connect(username=settings.ftp_username, password=settings.ftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    try:
        with sftp.file(_remote_path(settings, remote_name), "rb") as handle:
            return handle.read()
    finally:
        sftp.close()
        transport.close()


def _download_via_ftp(settings: Settings, remote_name: str) -> bytes:
    ftp = FTP()
    ftp.connect(settings.ftp_host, settings.ftp_port or 21, timeout=settings.ftp_timeout_seconds)
    ftp.login(settings.ftp_username, settings.ftp_password)
    chunks: list[bytes] = []
    try:
        ftp.retrbinary(f"RETR {_remote_path(settings, remote_name)}", chunks.append)
        return b"".join(chunks)
    finally:
        ftp.quit()


async def download_remote_file(settings: Settings, remote_name: str, destination: Path) -> Path:
    if not settings.ftp_host or not settings.ftp_username or not settings.ftp_password:
        raise RuntimeError("FTP credentials are not configured for supplier sync.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if settings.ftp_protocol == "sftp":
        payload = await asyncio.to_thread(_download_via_sftp, settings, remote_name)
    else:
        payload = await asyncio.to_thread(_download_via_ftp, settings, remote_name)
    destination.write_bytes(payload)
    return destination
