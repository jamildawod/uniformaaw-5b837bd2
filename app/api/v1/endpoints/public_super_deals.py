from fastapi import APIRouter, Depends

from app.api.deps import get_product_read_service
from app.schemas.product import ProductRead
from app.services.product_read_service import ProductReadService
from app.repositories.super_deal_repository import SuperDealRepository
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/super-deals", response_model=list[ProductRead])
async def get_super_deals(
    db: AsyncSession = Depends(get_db),
    service: ProductReadService = Depends(get_product_read_service),
) -> list[ProductRead]:
    repository = SuperDealRepository(db)
    product_ids = await repository.get_all_public_ids()
    return await service.list_public_products_by_ids(product_ids)
