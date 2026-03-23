from fastapi import APIRouter, Depends

from app.api.deps import get_product_read_service
from app.schemas.category import CategoryListItem
from app.services.product_read_service import ProductReadService

router = APIRouter()


@router.get("/categories", response_model=list[CategoryListItem])
async def list_categories(
    service: ProductReadService = Depends(get_product_read_service),
) -> list[CategoryListItem]:
    return await service.list_root_categories()


@router.get("/sectors", response_model=list[CategoryListItem])
async def list_sectors(
    service: ProductReadService = Depends(get_product_read_service),
) -> list[CategoryListItem]:
    return await service.list_sector_categories()
