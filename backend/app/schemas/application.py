from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ApplicationCreate(BaseModel):
    job_id: UUID
    message: Optional[str] = None
    proposed_price: Optional[Decimal] = None
    # New fields
    applicant_name: Optional[str] = None
    applicant_profile_image: Optional[str] = None
    applicant_vouch_count: Optional[int] = None
    portfolio_url: Optional[str] = None   # new

class ApplicationOut(BaseModel):
    id: UUID
    job_id: UUID
    applicant_id: UUID
    message: Optional[str] = None
    proposed_price: Optional[Decimal] = None
    created_at: datetime
    # New fields
    applicant_name: Optional[str] = None
    applicant_profile_image: Optional[str] = None
    applicant_vouch_count: Optional[int] = None
    portfolio_url: Optional[str] = None   # new

    class Config:
        from_attributes = True