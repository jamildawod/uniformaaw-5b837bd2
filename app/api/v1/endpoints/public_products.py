from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_product_read_service
from app.schemas.product import AutocompleteItem, FiltersRead, ProductRead, ProductVariantRead
from app.services.product_read_service import ProductReadService

router = APIRouter()


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    limit: int = Query(default=200, le=2000),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    color: str | None = Query(default=None),
    size: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    service: ProductReadService = Depends(get_product_read_service),
) -> list[ProductRead]:
    return await service.list_public_products(
        limit=limit,
        offset=offset,
        category_slug=category,
        sector_slug=sector,
        color=color,
        size=size,
        search=q,
    )


@router.get("/filters", response_model=FiltersRead)
async def get_filters(
    service: ProductReadService = Depends(get_product_read_service),
) -> FiltersRead:
    return await service.get_filters()


@router.get("/products/autocomplete", response_model=list[AutocompleteItem])
async def autocomplete_products(
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=8, le=20),
    service: ProductReadService = Depends(get_product_read_service),
) -> list[AutocompleteItem]:
    return await service.autocomplete(q=q, limit=limit)


@router.get("/products/{slug}", response_model=ProductRead)
async def get_product(
    slug: str,
    service: ProductReadService = Depends(get_product_read_service),
) -> ProductRead:
    try:
        product = await service.get_public_product(slug)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.get("/products/{slug}/variants", response_model=list[ProductVariantRead])
async def get_product_variants(
    slug: str,
    service: ProductReadService = Depends(get_product_read_service),
) -> list[ProductVariantRead]:
    try:
        variants = await service.get_public_variants(slug)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    if variants is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return variants
