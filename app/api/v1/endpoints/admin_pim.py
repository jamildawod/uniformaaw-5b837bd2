from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_superuser
from app.db.session import get_db
from app.models.user import User
from app.repositories.pim_lifecycle_status_repository import PimLifecycleStatusRepository
from app.services.pim_status_import import PimStatusImportService, PimStatusParseResult

router = APIRouter()


class PimStatusPreviewRowRead(BaseModel):
    item_no: str
    lifecycle_status: str
    is_visible: bool


class PimStatusSummaryRead(BaseModel):
    total_items: int
    active_items: int
    other_items: int
    latest_imported_at: datetime | None = None
    latest_source_file_name: str | None = None


class PimStatusPreviewRead(BaseModel):
    source_file_name: str
    total_rows: int
    importable_rows: int
    active_count: int
    other_status_count: int
    skipped_count: int
    preview_rows: list[PimStatusPreviewRowRead]


class PimStatusImportRead(PimStatusPreviewRead):
    imported_items: int
    summary: PimStatusSummaryRead


def _build_preview_response(parsed: PimStatusParseResult) -> PimStatusPreviewRead:
    return PimStatusPreviewRead(
        source_file_name=parsed.source_file_name,
        total_rows=parsed.total_rows,
        importable_rows=parsed.importable_rows,
        active_count=parsed.active_count,
        other_status_count=parsed.other_status_count,
        skipped_count=parsed.skipped_count,
        preview_rows=[
            PimStatusPreviewRowRead(
                item_no=row.item_no,
                lifecycle_status=row.lifecycle_status,
                is_visible=row.is_visible,
            )
            for row in parsed.preview_rows
        ],
    )


@router.get("/admin/pim-status/summary", response_model=PimStatusSummaryRead)
async def get_pim_status_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PimStatusSummaryRead:
    repository = PimLifecycleStatusRepository(db)
    return PimStatusSummaryRead(**await repository.get_summary())


@router.post("/admin/pim-status/preview", response_model=PimStatusPreviewRead)
async def preview_pim_status_import(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PimStatusPreviewRead:
    repository = PimLifecycleStatusRepository(db)
    service = PimStatusImportService(repository)
    try:
        parsed = await service.parse_upload(
            file_name=file.filename,
            content=await file.read(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _build_preview_response(parsed)


@router.post("/admin/pim-status/import", response_model=PimStatusImportRead)
async def import_pim_status(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> PimStatusImportRead:
    repository = PimLifecycleStatusRepository(db)
    service = PimStatusImportService(repository)
    try:
        parsed = await service.parse_upload(
            file_name=file.filename,
            content=await file.read(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    imported_items = await service.import_rows(parsed)
    await db.commit()
    summary = PimStatusSummaryRead(**await repository.get_summary())

    return PimStatusImportRead(
        **_build_preview_response(parsed).model_dump(),
        imported_items=imported_items,
        summary=summary,
    )
