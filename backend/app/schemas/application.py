from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ApplicationCreate(BaseModel):
    job_id: UUID
    message: Optional[str] = None
    proposed_price: Optional[Decimal] = None

class ApplicationOut(BaseModel):
    id: UUID
    job_id: UUID
    applicant_id: UUID
    message: Optional[str] = None
    proposed_price: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True