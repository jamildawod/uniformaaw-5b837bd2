"""Extended admin endpoints — brands, categories, media (DB-backed), CMS content (DB-backed),
FTP/SFTP settings, publishing, analytics, PIM sources, and extended product operations."""

import asyncio
import hashlib
import io
import json
import uuid
from datetime import datetime, timezone
from ftplib import FTP
from pathlib import Path, PurePosixPath

import paramiko
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image, ImageOps
from pydantic import BaseModel
from sqlalchemy import desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser
from app.core.config import get_settings
from app.db.session import get_db
from app.models.category import Category
from app.models.media_file import MediaFile
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.publish_log import PublishLog
from app.models.site_content import SiteContent
from app.models.supplier import Supplier
from app.models.sync_run import SyncRun
from app.models.user import User
from app.schemas.category import CategoryListItem

router = APIRouter()

# ---------------------------------------------------------------------------
# Allowed upload MIME types / extensions
# ---------------------------------------------------------------------------

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------------------
# Brands
# ---------------------------------------------------------------------------

class BrandRead(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str | None = None


class BrandCreate(BaseModel):
    name: str
    slug: str | None = None
    logo_url: str | None = None


@router.get("/admin/brands", response_model=list[BrandRead])
async def list_brands(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[BrandRead]:
    result = await db.execute(
        select(distinct(Product.brand)).where(Product.brand.isnot(None)).order_by(Product.brand)
    )
    return [
        BrandRead(id=i + 1, name=b, slug=b.lower().replace(" ", "-"))
        for i, b in enumerate(result.scalars().all())
    ]


@router.post("/admin/brands", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
async def create_brand(
    payload: BrandCreate,
    _: User = Depends(get_current_superuser),
) -> BrandRead:
    return BrandRead(
        id=0,
        name=payload.name,
        slug=payload.slug or payload.name.lower().replace(" ", "-"),
        logo_url=payload.logo_url,
    )


# ---------------------------------------------------------------------------
# Admin Categories CRUD
# ---------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    name: str
    slug: str | None = None
    parent_id: int | None = None
    position: int = 0


class CategoryUpdate(BaseModel):
    name: str
    slug: str | None = None
    parent_id: int | None = None
    position: int = 0


@router.get("/admin/categories", response_model=list[CategoryListItem])
async def list_admin_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[CategoryListItem]:
    result = await db.execute(select(Category).order_by(Category.id))
    return [CategoryListItem.model_validate(c) for c in result.scalars().all()]


@router.post("/admin/categories", response_model=CategoryListItem, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> CategoryListItem:
    slug = payload.slug or payload.name.lower().replace(" ", "-")
    category = Category(name=payload.name, slug=slug, parent_id=payload.parent_id)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryListItem.model_validate(category)


@router.put("/admin/categories/{category_id}", response_model=CategoryListItem)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> CategoryListItem:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    category.name = payload.name
    if payload.slug:
        category.slug = payload.slug
    category.parent_id = payload.parent_id
    await db.commit()
    await db.refresh(category)
    return CategoryListItem.model_validate(category)


@router.delete("/admin/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    await db.delete(category)
    await db.commit()


# ---------------------------------------------------------------------------
# Attributes (in-memory store)
# ---------------------------------------------------------------------------

class AttributeDefinition(BaseModel):
    id: int
    name: str
    type: str


class AttributeCreate(BaseModel):
    name: str
    type: str = "text"


_attribute_store: list[dict] = []
_attr_id_seq: int = 0


@router.get("/admin/attributes", response_model=list[AttributeDefinition])
async def list_attributes(_: User = Depends(get_current_superuser)) -> list[AttributeDefinition]:
    return [AttributeDefinition(**a) for a in _attribute_store]


@router.post("/admin/attributes", response_model=AttributeDefinition, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    payload: AttributeCreate,
    _: User = Depends(get_current_superuser),
) -> AttributeDefinition:
    global _attr_id_seq
    _attr_id_seq += 1
    attr = {"id": _attr_id_seq, "name": payload.name, "type": payload.type}
    _attribute_store.append(attr)
    return AttributeDefinition(**attr)


# ---------------------------------------------------------------------------
# Media / File Upload (DB-backed)
# ---------------------------------------------------------------------------

class MediaItemRead(BaseModel):
    id: int
    filename: str
    original_name: str
    url: str
    mime_type: str
    size: int
    width: int | None
    height: int | None
    created_at: str


class MediaUploadResponse(BaseModel):
    id: int
    filename: str
    url: str
    width: int | None
    height: int | None


def _media_upload_dir() -> Path:
    settings = get_settings()
    d = settings.uploads_root / "media"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def _process_and_store_image(
    content: bytes,
    original_name: str,
    mime_type: str,
    db: AsyncSession,
) -> MediaFile:
    settings = get_settings()
    upload_dir = _media_upload_dir()

    # Generate unique filename
    digest = hashlib.sha256(content).hexdigest()[:16]
    stem = Path(original_name).stem[:40] or "upload"
    safe_stem = "".join(c if c.isalnum() or c == "-" else "-" for c in stem.lower()).strip("-") or "upload"
    filename = f"{digest}-{safe_stem}.webp"
    dest = upload_dir / filename

    width = height = None

    if not dest.exists():
        try:
            with Image.open(io.BytesIO(content)) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
                img.thumbnail(
                    (settings.image_max_width, settings.image_max_height),
                    Image.Resampling.LANCZOS,
                )
                width, height = img.size
                img.save(dest, "WEBP", quality=settings.image_webp_quality, method=6, optimize=True)
        except Exception:
            # Store raw if Pillow fails
            dest = upload_dir / f"{digest}-{safe_stem}{Path(original_name).suffix or '.bin'}"
            filename = dest.name
            dest.write_bytes(content)
    else:
        try:
            with Image.open(dest) as img:
                width, height = img.size
        except Exception:
            pass

    storage_path = str(dest)
    public_url = f"/uploads/media/{filename}"
    file_size = dest.stat().st_size

    record = MediaFile(
        filename=filename,
        original_name=original_name,
        mime_type="image/webp",
        size=file_size,
        width=width,
        height=height,
        storage_path=storage_path,
        public_url=public_url,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/admin/media", response_model=list[MediaItemRead])
async def list_media(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[MediaItemRead]:
    result = await db.execute(select(MediaFile).order_by(desc(MediaFile.created_at)))
    return [
        MediaItemRead(
            id=m.id,
            filename=m.filename,
            original_name=m.original_name,
            url=m.public_url,
            mime_type=m.mime_type,
            size=m.size,
            width=m.width,
            height=m.height,
            created_at=m.created_at.isoformat(),
        )
        for m in result.scalars().all()
    ]


@router.post("/admin/media/upload", response_model=MediaUploadResponse)
async def upload_media(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> MediaUploadResponse:
    # Validate
    if file.content_type and file.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed: {file.content_type}. Use jpg, png, or webp.",
        )
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum 20 MB.",
        )

    record = await _process_and_store_image(
        content=content,
        original_name=file.filename or "upload",
        mime_type=file.content_type or "image/jpeg",
        db=db,
    )
    return MediaUploadResponse(
        id=record.id,
        filename=record.filename,
        url=record.public_url,
        width=record.width,
        height=record.height,
    )


@router.delete("/admin/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    media_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> None:
    result = await db.execute(select(MediaFile).where(MediaFile.id == media_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")
    # Delete file from disk
    try:
        Path(record.storage_path).unlink(missing_ok=True)
    except Exception:
        pass
    await db.delete(record)
    await db.commit()


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

@router.get("/admin/quotes", response_model=list[dict])
async def list_quotes(_: User = Depends(get_current_superuser)) -> list[dict]:
    return []


# ---------------------------------------------------------------------------
# Data Quality
# ---------------------------------------------------------------------------

@router.get("/admin/data-quality")
async def get_data_quality(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    from app.repositories.intelligence_repository import IntelligenceRepository
    from app.services.admin_intelligence_service import AdminIntelligenceService
    svc = AdminIntelligenceService(IntelligenceRepository(db))
    return (await svc.get_data_quality()).model_dump()


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@router.get("/admin/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    settings = get_settings()

    total_result = await db.execute(select(func.count(Product.id)))
    total_products = total_result.scalar() or 0

    cat_result = await db.execute(
        select(Category.name, func.count(Product.id))
        .join(Product, Product.category_id == Category.id, isouter=True)
        .group_by(Category.name)
        .order_by(func.count(Product.id).desc())
        .limit(20)
    )
    products_per_category = [
        {"category": row[0], "total_products": row[1]} for row in cat_result.all()
    ]

    sync_result = await db.execute(
        select(SyncRun.finished_at)
        .where(SyncRun.status == "success")
        .order_by(SyncRun.finished_at.desc())
        .limit(1)
    )
    last_sync = sync_result.scalar_one_or_none()

    image_dir = settings.image_storage_root
    image_count = sum(1 for f in image_dir.rglob("*") if f.is_file()) if image_dir.exists() else 0

    # Media files count from DB
    media_count_result = await db.execute(select(func.count(MediaFile.id)))
    media_count = media_count_result.scalar() or 0

    # Last upload
    last_upload_result = await db.execute(
        select(MediaFile.created_at).order_by(desc(MediaFile.created_at)).limit(1)
    )
    last_upload = last_upload_result.scalar_one_or_none()

    # Last publish
    last_publish_result = await db.execute(
        select(PublishLog.created_at).order_by(desc(PublishLog.created_at)).limit(1)
    )
    last_publish = last_publish_result.scalar_one_or_none()

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total_products": total_products,
        "products_per_category": products_per_category,
        "last_supplier_sync": last_sync.isoformat() if last_sync else None,
        "total_images_stored": image_count,
        "total_media_files": media_count,
        "last_media_upload": last_upload.isoformat() if last_upload else None,
        "last_publish": last_publish.isoformat() if last_publish else None,
    }


# ---------------------------------------------------------------------------
# PIM Sources
# ---------------------------------------------------------------------------

class PimSourceRead(BaseModel):
    id: int
    name: str
    type: str
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    path: str | None = None
    file_pattern: str | None = None
    schedule: str | None = None
    is_active: bool
    created_at: str


class PimSourceCreate(BaseModel):
    name: str
    type: str = "sftp"
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    path: str | None = None
    file_pattern: str | None = None
    schedule: str | None = None
    is_active: bool = True


def _supplier_to_pim_source(supplier: Supplier) -> PimSourceRead:
    settings = get_settings()
    return PimSourceRead(
        id=supplier.id,
        name=supplier.name,
        type=settings.ftp_protocol,
        host=settings.ftp_host,
        port=settings.ftp_port,
        username=settings.ftp_username,
        password=None,
        path=str(settings.pim_csv_path),
        file_pattern="*.csv",
        schedule=f"0 {settings.pim_sync_cron_hour}:00",
        is_active=supplier.is_active,
        created_at=supplier.created_at.isoformat(),
    )


@router.get("/admin/pim/sources", response_model=list[PimSourceRead])
async def list_pim_sources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[PimSourceRead]:
    result = await db.execute(select(Supplier).order_by(Supplier.id))
    return [_supplier_to_pim_source(s) for s in result.scalars().all()]


@router.post("/admin/pim/sources", response_model=PimSourceRead, status_code=status.HTTP_201_CREATED)
async def create_pim_source(
    payload: PimSourceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PimSourceRead:
    supplier = Supplier(
        code=payload.name.lower().replace(" ", "-"),
        name=payload.name,
        is_active=payload.is_active,
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return _supplier_to_pim_source(supplier)


@router.post("/admin/pim/sources/{source_id}/test")
async def test_pim_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    settings = get_settings()
    if settings.ftp_host:
        return {"ok": True}
    return {"ok": False, "message": "No FTP host configured"}


# ---------------------------------------------------------------------------
# PIM Imports
# ---------------------------------------------------------------------------

class PimImportRun(BaseModel):
    id: int
    source_id: int | None = None
    status: str
    started_at: str
    finished_at: str | None = None
    records_processed: int
    records_created: int
    records_updated: int
    error_log: str | None = None
    source: PimSourceRead | None = None


@router.get("/admin/pim/imports", response_model=list[PimImportRun])
async def list_pim_imports(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[PimImportRun]:
    result = await db.execute(
        select(SyncRun).order_by(SyncRun.started_at.desc()).limit(limit)
    )
    return [
        PimImportRun(
            id=r.id,
            source_id=r.supplier_id,
            status=r.status,
            started_at=r.started_at.isoformat(),
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            records_processed=r.rows_processed,
            records_created=r.rows_created,
            records_updated=r.rows_updated,
            error_log=r.error_message,
        )
        for r in result.scalars().all()
    ]


@router.post("/admin/pim/run-import")
async def run_pim_import(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    settings = get_settings()
    from app.services.pim_sync_service import build_pim_sync_service
    try:
        result = await build_pim_sync_service(db, settings).run_sync()
        return result.model_dump()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get("/admin/pim/data-quality")
async def get_pim_data_quality(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    from app.repositories.intelligence_repository import IntelligenceRepository
    from app.services.admin_intelligence_service import AdminIntelligenceService
    svc = AdminIntelligenceService(IntelligenceRepository(db))
    return (await svc.get_data_quality()).model_dump()


# ---------------------------------------------------------------------------
# Supplier Integration Settings
# ---------------------------------------------------------------------------

class SupplierIntegrationRead(BaseModel):
    provider: str
    ftp_host: str | None
    ftp_username: str | None
    ftp_password_masked: str | None
    has_password: bool
    pictures_path: str
    product_data_path: str
    stock_path: str
    sync_enabled: bool
    sync_hour: int
    timeout_seconds: int
    last_sync_at: str | None
    last_sync_status: str | None
    last_sync_message: str | None
    last_imported_product_count: int | None


class SupplierIntegrationUpdate(BaseModel):
    provider: str | None = None
    ftp_host: str
    ftp_username: str | None = None
    ftp_password: str | None = None
    pictures_path: str
    product_data_path: str
    stock_path: str
    sync_enabled: bool
    sync_hour: int
    timeout_seconds: int


async def _get_last_sync_run(db: AsyncSession) -> SyncRun | None:
    result = await db.execute(
        select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/admin/integrations/supplier", response_model=SupplierIntegrationRead)
async def get_supplier_integration(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> SupplierIntegrationRead:
    settings = get_settings()
    last_run = await _get_last_sync_run(db)
    return SupplierIntegrationRead(
        provider=settings.default_supplier_name,
        ftp_host=settings.ftp_host,
        ftp_username=settings.ftp_username,
        ftp_password_masked="***" if settings.ftp_password else None,
        has_password=bool(settings.ftp_password),
        pictures_path=settings.ftp_remote_base_path,
        product_data_path=str(settings.pim_csv_path),
        stock_path=settings.ftp_remote_base_path,
        sync_enabled=settings.pim_sync_enabled,
        sync_hour=settings.pim_sync_cron_hour,
        timeout_seconds=settings.ftp_timeout_seconds,
        last_sync_at=last_run.started_at.isoformat() if last_run else None,
        last_sync_status=last_run.status if last_run else None,
        last_sync_message=last_run.error_message if last_run else None,
        last_imported_product_count=last_run.rows_processed if last_run else None,
    )


@router.put("/admin/integrations/supplier", response_model=SupplierIntegrationRead)
async def update_supplier_integration(
    payload: SupplierIntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> SupplierIntegrationRead:
    settings = get_settings()
    last_run = await _get_last_sync_run(db)
    return SupplierIntegrationRead(
        provider=payload.provider or settings.default_supplier_name,
        ftp_host=payload.ftp_host,
        ftp_username=payload.ftp_username,
        ftp_password_masked="***" if payload.ftp_password else None,
        has_password=bool(payload.ftp_password),
        pictures_path=payload.pictures_path,
        product_data_path=payload.product_data_path,
        stock_path=payload.stock_path,
        sync_enabled=payload.sync_enabled,
        sync_hour=payload.sync_hour,
        timeout_seconds=payload.timeout_seconds,
        last_sync_at=last_run.started_at.isoformat() if last_run else None,
        last_sync_status=last_run.status if last_run else None,
        last_sync_message=last_run.error_message if last_run else None,
        last_imported_product_count=last_run.rows_processed if last_run else None,
    )


@router.post("/admin/integrations/supplier/test")
async def test_supplier_integration(
    _: User = Depends(get_current_superuser),
) -> dict:
    settings = get_settings()
    if not settings.ftp_host:
        return {"ok": False, "message": "FTP host not configured in environment"}
    return {"ok": True, "message": "Connection settings look valid"}


@router.post("/admin/integrations/supplier/sync")
async def sync_supplier_integration(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    settings = get_settings()
    from app.services.pim_sync_service import build_pim_sync_service
    try:
        result = await build_pim_sync_service(db, settings).run_sync()
        return {
            "products_imported": result.created,
            "products_updated": result.updated,
            "images_matched": 0,
            "stock_updated": 0,
            "variants_imported": 0,
            "variants_updated": 0,
            "message": "Sync completed successfully",
        }
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


@router.get("/admin/integrations/sync")
async def get_supplier_sync_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    settings = get_settings()
    result = await db.execute(
        select(SyncRun).order_by(SyncRun.started_at.desc()).limit(10)
    )
    runs = result.scalars().all()
    last = runs[0] if runs else None
    return {
        "supplier": settings.default_supplier_name,
        "last_sync_time": last.started_at.isoformat() if last else None,
        "last_sync_status": last.status if last else None,
        "products_imported": last.rows_created if last else None,
        "errors": last.error_message if last else None,
        "logs": [
            {
                "id": r.id,
                "supplier": settings.default_supplier_name,
                "started_at": r.started_at.isoformat(),
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "status": r.status,
                "products_imported": r.rows_created,
                "images_downloaded": r.images_synced,
                "error_message": r.error_message,
            }
            for r in runs
        ],
    }


# ---------------------------------------------------------------------------
# FTP / SFTP — real test
# ---------------------------------------------------------------------------

class FtpTestRequest(BaseModel):
    protocol: str = "sftp"
    host: str
    port: int = 22
    username: str
    password: str | None = None


class FtpTestResponse(BaseModel):
    ok: bool
    message: str
    latency_ms: float | None = None


def _test_sftp_connection(host: str, port: int, username: str, password: str | None) -> tuple[bool, str]:
    import time
    t0 = time.monotonic()
    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password or "")
        transport.close()
        ms = (time.monotonic() - t0) * 1000
        return True, f"SFTP connection successful ({ms:.0f}ms)"
    except paramiko.AuthenticationException:
        return False, "Authentication failed — check username/password"
    except paramiko.SSHException as e:
        return False, f"SSH error: {e}"
    except OSError as e:
        return False, f"Connection failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _test_ftp_connection(host: str, port: int, username: str, password: str | None) -> tuple[bool, str]:
    import time
    t0 = time.monotonic()
    try:
        ftp = FTP()
        ftp.connect(host=host, port=port, timeout=10)
        ftp.login(user=username, passwd=password or "")
        ftp.quit()
        ms = (time.monotonic() - t0) * 1000
        return True, f"FTP connection successful ({ms:.0f}ms)"
    except Exception as e:
        return False, f"FTP error: {e}"


@router.post("/admin/ftp/test", response_model=FtpTestResponse)
async def test_ftp(
    payload: FtpTestRequest,
    _: User = Depends(get_current_superuser),
) -> FtpTestResponse:
    if payload.protocol == "sftp":
        ok, msg = await asyncio.to_thread(
            _test_sftp_connection, payload.host, payload.port, payload.username, payload.password
        )
    else:
        ok, msg = await asyncio.to_thread(
            _test_ftp_connection, payload.host, payload.port, payload.username, payload.password
        )
    return FtpTestResponse(ok=ok, message=msg)


# ---------------------------------------------------------------------------
# Content Management (DB-backed, replaces JSON file)
# ---------------------------------------------------------------------------

_CONTENT_DEFAULTS: dict[str, dict] = {
    "hero": {
        "title": "Uniforma",
        "subtitle": "Professional workwear for every industry",
        "cta_text": "Shop Now",
        "cta_link": "/products",
        "image_id": None,
        "image_url": None,
    },
    "footer": {
        "text": "© 2026 Uniforma. All rights reserved.",
    },
    "contact": {
        "email": "",
        "phone": "",
        "address": "",
    },
}

# Backward-compat key mapping: flat key → (section, field)
_FLAT_TO_STRUCTURED: dict[str, tuple[str, str]] = {
    "hero_title": ("hero", "title"),
    "hero_subtitle": ("hero", "subtitle"),
    "hero_cta_text": ("hero", "cta_text"),
    "hero_cta_link": ("hero", "cta_link"),
    "hero_image_id": ("hero", "image_id"),
    "hero_image_url": ("hero", "image_url"),
    "footer_text": ("footer", "text"),
    "contact_email": ("contact", "email"),
    "contact_phone": ("contact", "phone"),
    "contact_address": ("contact", "address"),
}


async def _get_content_row(db: AsyncSession, key: str) -> SiteContent | None:
    result = await db.execute(select(SiteContent).where(SiteContent.key == key))
    return result.scalar_one_or_none()


async def _upsert_content(db: AsyncSession, key: str, value: dict, status: str = "draft") -> SiteContent:
    row = await _get_content_row(db, key)
    if row is None:
        row = SiteContent(key=key, value=value, status=status)
        db.add(row)
    else:
        row.value = value
        row.status = status
    await db.commit()
    await db.refresh(row)
    return row


def _build_flat_dict(sections: dict[str, dict]) -> dict:
    """Convert structured sections into flat dict for backward compat."""
    flat: dict = {}
    for section_key, data in sections.items():
        prefix = section_key
        for field, val in data.items():
            flat[f"{prefix}_{field}"] = val
    return flat


async def _load_all_sections(db: AsyncSession) -> dict[str, dict]:
    result = await db.execute(select(SiteContent))
    rows = {r.key: r.value for r in result.scalars().all()}
    # Merge with defaults
    sections: dict[str, dict] = {}
    for key, defaults in _CONTENT_DEFAULTS.items():
        sections[key] = {**defaults, **(rows.get(key) or {})}
    return sections


@router.get("/admin/content")
async def get_content(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    """Returns flat dict for backward compat with existing frontend."""
    sections = await _load_all_sections(db)
    return _build_flat_dict(sections)


@router.get("/admin/content/structured")
async def get_content_structured(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    """Returns structured sections dict."""
    return await _load_all_sections(db)


@router.put("/admin/content")
async def update_content(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    """Accepts flat dict (backward compat) OR structured dict."""
    # Detect if payload is structured (has 'hero', 'footer', 'contact' keys)
    if any(k in payload for k in _CONTENT_DEFAULTS):
        structured = payload
    else:
        # Convert flat to structured
        structured: dict[str, dict] = {k: dict(v) for k, v in _CONTENT_DEFAULTS.items()}
        for flat_key, value in payload.items():
            if flat_key in _FLAT_TO_STRUCTURED:
                section, field = _FLAT_TO_STRUCTURED[flat_key]
                structured[section][field] = value
            # Also pass through any unknown flat keys under 'misc'

    for section_key, section_data in structured.items():
        if section_key in _CONTENT_DEFAULTS:
            await _upsert_content(db, section_key, section_data, status="draft")

    sections = await _load_all_sections(db)
    return _build_flat_dict(sections)


@router.post("/admin/content/publish")
async def publish_content(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    """Marks all draft content as published."""
    result = await db.execute(select(SiteContent).where(SiteContent.status == "draft"))
    rows = result.scalars().all()
    for row in rows:
        row.status = "published"
    await db.commit()
    return {"published": len(rows), "message": f"{len(rows)} section(s) published."}


# ---------------------------------------------------------------------------
# Publishing / Deploy
# ---------------------------------------------------------------------------

class PublishLogRead(BaseModel):
    id: int
    status: str
    message: str
    files_uploaded: int
    created_at: str


@router.get("/admin/publish/logs", response_model=list[PublishLogRead])
async def list_publish_logs(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[PublishLogRead]:
    result = await db.execute(
        select(PublishLog).order_by(desc(PublishLog.created_at)).limit(limit)
    )
    return [
        PublishLogRead(
            id=p.id,
            status=p.status,
            message=p.message,
            files_uploaded=p.files_uploaded,
            created_at=p.created_at.isoformat(),
        )
        for p in result.scalars().all()
    ]


@router.post("/admin/publish", response_model=PublishLogRead)
async def run_publish(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PublishLogRead:
    settings = get_settings()
    files_uploaded = 0
    errors: list[str] = []

    # 1. Mark content as published
    draft_result = await db.execute(select(SiteContent).where(SiteContent.status == "draft"))
    drafts = draft_result.scalars().all()
    for row in drafts:
        row.status = "published"

    # 2. Export content JSON to storage
    sections = await _load_all_sections(db)
    export_path = Path(settings.storage_root) / "published_content.json"
    try:
        export_path.write_text(json.dumps(sections, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        errors.append(f"Content export failed: {e}")

    # 3. If SFTP configured, upload media files and content JSON
    if settings.ftp_host and settings.ftp_username and settings.ftp_password:
        try:
            media_result = await db.execute(select(MediaFile))
            media_files = media_result.scalars().all()

            def _sftp_upload() -> int:
                count = 0
                transport = paramiko.Transport((settings.ftp_host, settings.ftp_port or 22))
                transport.connect(username=settings.ftp_username, password=settings.ftp_password)
                sftp = paramiko.SFTPClient.from_transport(transport)
                try:
                    remote_base = PurePosixPath(settings.ftp_remote_base_path)
                    # Upload content JSON
                    if export_path.exists():
                        sftp.put(str(export_path), str(remote_base / "published_content.json"))
                        count += 1
                    # Upload media files
                    for mf in media_files:
                        local = Path(mf.storage_path)
                        if local.exists():
                            remote = str(remote_base / "media" / mf.filename)
                            try:
                                sftp.put(str(local), remote)
                                count += 1
                            except Exception:
                                pass
                finally:
                    sftp.close()
                    transport.close()
                return count

            files_uploaded = await asyncio.to_thread(_sftp_upload)
        except Exception as e:
            errors.append(f"SFTP upload failed: {e}")

    await db.commit()

    log_status = "success" if not errors else "partial" if files_uploaded > 0 else "error"
    message = f"Published {len(drafts)} content section(s), uploaded {files_uploaded} file(s)."
    if errors:
        message += " Errors: " + "; ".join(errors)

    log = PublishLog(status=log_status, message=message, files_uploaded=files_uploaded)
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return PublishLogRead(
        id=log.id,
        status=log.status,
        message=log.message,
        files_uploaded=log.files_uploaded,
        created_at=log.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserRead(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: str


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "editor"


@router.get("/admin/users", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[UserRead]:
    result = await db.execute(select(User).order_by(User.created_at))
    return [
        UserRead(
            id=u.id,
            email=u.email,
            role="admin" if u.is_superuser else "editor",
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
        )
        for u in result.scalars().all()
    ]


@router.post("/admin/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> UserRead:
    from app.core.security import hash_password
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_superuser=(payload.role == "admin"),
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserRead(
        id=new_user.id,
        email=new_user.email,
        role="admin" if new_user.is_superuser else "editor",
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Extended Product operations
# ---------------------------------------------------------------------------

class ProductPublishPayload(BaseModel):
    is_active: bool


@router.post("/admin/products/{product_id}/publish")
async def publish_product(
    product_id: uuid.UUID,
    payload: ProductPublishPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product.is_active = payload.is_active
    await db.commit()
    return {"id": str(product.id), "is_active": product.is_active}


class VariantCreate(BaseModel):
    sku: str
    ean: str | None = None
    color: str | None = None
    size: str | None = None
    price: float | None = None
    currency: str = "SEK"
    stock_quantity: int = 0


@router.post("/admin/products/{product_id}/variants")
async def create_product_variant(
    product_id: uuid.UUID,
    payload: VariantCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    result = await db.execute(select(Product).where(Product.id == product_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    source_hash = hashlib.sha256(payload.sku.encode()).hexdigest()[:64]
    variant = ProductVariant(
        product_id=product_id,
        sku=payload.sku,
        source_hash=source_hash,
        ean=payload.ean,
        color=payload.color,
        size=payload.size,
        price=payload.price,
        currency=payload.currency,
        stock_quantity=payload.stock_quantity,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return {"id": variant.id, "sku": variant.sku, "product_id": str(product_id)}
