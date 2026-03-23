import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    org_number: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=64)
    subject: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1)

    @field_validator("name", "company", "org_number", "phone", "subject", "message", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank.")
        return stripped

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, value: str) -> str:
        allowed = {"offert", "produktfraga", "ovrigt"}
        if value not in allowed:
            raise ValueError(f"Subject must be one of: {', '.join(sorted(allowed))}")
        return value


class InquiryRead(BaseModel):
    id: uuid.UUID
    name: str
    company: str
    org_number: str
    email: str
    phone: str
    subject: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
