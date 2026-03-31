from sqlalchemy import String, cast, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pim_lifecycle_status import PimLifecycleStatus
from app.models.product import Product
from app.models.super_deal import SuperDeal


class SuperDealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def replace_all(self, product_ids: list[str]) -> None:
        await self.session.execute(delete(SuperDeal))

        seen: set[str] = set()
        for product_id in product_ids:
            if product_id in seen:
                continue
            seen.add(product_id)
            self.session.add(SuperDeal(product_id=product_id))

        await self.session.flush()

    async def get_all_ids(self) -> list[str]:
        result = await self.session.execute(
            select(SuperDeal.product_id).order_by(SuperDeal.id.asc())
        )
        return list(result.scalars().all())

    async def get_all_public_ids(self) -> list[str]:
        result = await self.session.execute(
            select(SuperDeal.product_id)
            .join(Product, cast(Product.id, String(36)) == SuperDeal.product_id)
            .join(PimLifecycleStatus, PimLifecycleStatus.item_no == Product.external_id)
            .where(func.lower(PimLifecycleStatus.lifecycle_status) == "active")
            .order_by(SuperDeal.id.asc())
        )
        return list(result.scalars().all())
