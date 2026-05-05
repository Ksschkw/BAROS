from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class CategoryOut(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True