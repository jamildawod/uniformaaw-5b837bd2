from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, desc, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pim_lifecycle_status import PimLifecycleStatus


class PimLifecycleStatusRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_upsert(
        self,
        rows: list[dict[str, str]],
        *,
        source_file_name: str | None,
        updated_at: datetime,
    ) -> int:
        if not rows:
            return 0

        values = [
            {
                "item_no": row["item_no"],
                "lifecycle_status": row["lifecycle_status"],
                "source_file_name": source_file_name,
                "updated_at": updated_at,
            }
            for row in rows
        ]
        statement = insert(PimLifecycleStatus).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=[PimLifecycleStatus.item_no],
            set_={
                "lifecycle_status": statement.excluded.lifecycle_status,
                "source_file_name": statement.excluded.source_file_name,
                "updated_at": statement.excluded.updated_at,
            },
        )
        await self.session.execute(statement)
        await self.session.flush()
        return len(rows)

    async def get_summary(self) -> dict[str, object]:
        normalized_status = func.lower(func.coalesce(PimLifecycleStatus.lifecycle_status, ""))
        counts_result = await self.session.execute(
            select(
                func.count(PimLifecycleStatus.id),
                func.coalesce(
                    func.sum(case((normalized_status == "active", 1), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((normalized_status != "active", 1), else_=0)),
                    0,
                ),
                func.max(PimLifecycleStatus.updated_at),
            )
        )
        total_items, active_items, other_items, latest_imported_at = counts_result.one()

        latest_source_file_name = await self.session.scalar(
            select(PimLifecycleStatus.source_file_name)
            .order_by(desc(PimLifecycleStatus.updated_at), desc(PimLifecycleStatus.id))
            .limit(1)
        )

        return {
            "total_items": int(total_items or 0),
            "active_items": int(active_items or 0),
            "other_items": int(other_items or 0),
            "latest_imported_at": latest_imported_at,
            "latest_source_file_name": latest_source_file_name,
        }
