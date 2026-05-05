from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ScopeAmendmentCreate(BaseModel):
    job_id: UUID
    proposed_by: str  # "provider" or "client"
    reason: str
    additional_cost: Optional[Decimal] = None
    new_total_price: Decimal

class ScopeAmendmentAccept(BaseModel):
    accept: bool

class ScopeAmendmentOut(BaseModel):
    id: UUID
    job_id: UUID
    proposed_by: str
    reason: str
    additional_cost: Optional[Decimal] = None
    new_total_price: Decimal
    is_accepted: Optional[bool] = None
    created_at: datetime

    class Config:
        from_attributes = True