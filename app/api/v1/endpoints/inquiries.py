from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryCreate, InquiryRead

router = APIRouter()


@router.post("/inquiries", response_model=InquiryRead, status_code=201)
async def create_inquiry(
    payload: InquiryCreate,
    db: AsyncSession = Depends(get_db),
) -> InquiryRead:
    inquiry = Inquiry(
        name=payload.name,
        company=payload.company,
        org_number=payload.org_number,
        email=payload.email,
        phone=payload.phone,
        subject=payload.subject,
        message=payload.message,
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return InquiryRead.model_validate(inquiry)
