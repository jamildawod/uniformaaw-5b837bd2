import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser, get_product_read_service
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.admin_override_repository import AdminOverrideRepository
from app.repositories.intelligence_repository import IntelligenceRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.intelligence import SyncRun as SyncRunRead
from app.schemas.product import (
    AdminImageCreateRequest,
    AdminImageReorderRequest,
    AdminOverridePatchRequest,
    AdminProductRead,
    AdminProductUpdateRequest,
    AdminVariantUpdateRequest,
)
from app.schemas.sync import PimSyncResponse
from app.services.ftp_image_service import FtpImageService
from app.services.image_service import ImageService
from app.services.pim_sync_service import build_pim_sync_service
from app.services.product_read_service import ProductReadService

router = APIRouter()


@router.get("/admin/products", response_model=list[AdminProductRead])
async def list_admin_products(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    has_override: bool | None = Query(default=None),
    _: User = Depends(get_current_superuser),
    service: ProductReadService = Depends(get_product_read_service),
) -> list[AdminProductRead]:
    return await service.list_admin_products(
        limit=limit,
        offset=offset,
        search=search,
        category_id=category_id,
        is_active=is_active,
        has_override=has_override,
    )


@router.get("/admin/products/{product_id}", response_model=AdminProductRead)
async def get_admin_product(
    product_id: uuid.UUID,
    _: User = Depends(get_current_superuser),
    service: ProductReadService = Depends(get_product_read_service),
) -> AdminProductRead:
    product = await service.get_admin_product(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.patch("/admin/products/{product_id}", response_model=AdminProductRead)
async def patch_admin_product(
    product_id: uuid.UUID,
    payload: AdminOverridePatchRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.patch_admin_product(product_id, payload, updated_by=user.email)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.put("/admin/products/{product_id}", response_model=AdminProductRead)
async def update_admin_product(
    product_id: uuid.UUID,
    payload: AdminProductUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.update_admin_product(product_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.post("/admin/products/{product_id}/image", response_model=AdminProductRead)
async def add_product_image(
    product_id: uuid.UUID,
    payload: AdminImageCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.add_product_image(product_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.put("/admin/products/{product_id}/variants/{variant_id}", response_model=AdminProductRead)
async def update_product_variant(
    product_id: uuid.UUID,
    variant_id: int,
    payload: AdminVariantUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.update_admin_variant(product_id, variant_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.delete("/admin/products/{product_id}/variants/{variant_id}", response_model=AdminProductRead)
async def delete_product_variant(
    product_id: uuid.UUID,
    variant_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.delete_admin_variant(product_id, variant_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.post("/admin/products/{product_id}/images/{image_id}/primary", response_model=AdminProductRead)
async def set_product_image_primary(
    product_id: uuid.UUID,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.set_primary_product_image(product_id, image_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.delete("/admin/products/{product_id}/images/{image_id}", response_model=AdminProductRead)
async def delete_product_image(
    product_id: uuid.UUID,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.delete_product_image(product_id, image_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.post("/admin/products/{product_id}/images/reorder", response_model=AdminProductRead)
async def reorder_product_images(
    product_id: uuid.UUID,
    payload: AdminImageReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> AdminProductRead:
    service = ProductReadService(
        ProductRepository(db),
        AdminOverrideRepository(db),
    )
    product = await service.reorder_product_images(product_id, payload)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    await db.commit()
    return product


@router.post("/admin/images/sync")
async def sync_images(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    """Trigger image download sync independently of full PIM ingestion."""
    settings = get_settings()
    product_repository = ProductRepository(db)
    downloaded = await FtpImageService(
        db,
        product_repository,
        settings,
        ImageService(settings),
    ).sync_images()
    return {"downloaded": downloaded}


@router.post("/admin/sync/pim", response_model=PimSyncResponse)
async def sync_pim(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PimSyncResponse:
    settings = get_settings()
    try:
        return await build_pim_sync_service(db, settings).run_sync()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/admin/sync/runs", response_model=list[SyncRunRead])
async def list_sync_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> list[SyncRunRead]:
    repository = IntelligenceRepository(db)
    runs = await repository.fetch_recent_sync_runs(limit=limit, offset=offset)
    return [SyncRunRead(**run) for run in runs]
