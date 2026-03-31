from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser
from app.db.session import get_db
from app.models.user import User
from app.repositories.super_deal_repository import SuperDealRepository

router = APIRouter()


@router.post("/admin/super-deals")
async def save_super_deals(
    product_ids: list[str],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict[str, str]:
    repository = SuperDealRepository(db)
    await repository.replace_all(product_ids)
    await db.commit()
    return {"status": "ok"}
