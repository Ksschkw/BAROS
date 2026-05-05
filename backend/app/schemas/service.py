from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class ServiceCreate(BaseModel):
    category_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal
    latitude: float
    longitude: float
    radius_km: Optional[Decimal] = Decimal("5.0")

class ServiceUpdate(BaseModel):
    category_id: Optional[UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[Decimal] = None

class ServiceOut(BaseModel):
    id: UUID
    provider_id: UUID
    category_id: UUID
    title: str
    description: Optional[str] = None
    price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    latitude: float
    longitude: float
    radius_km: Decimal

    class Config:
        from_attributes = True