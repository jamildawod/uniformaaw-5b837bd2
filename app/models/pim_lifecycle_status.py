from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PimLifecycleStatus(Base):
    __tablename__ = "pim_lifecycle_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_no: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    lifecycle_status: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    source_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
