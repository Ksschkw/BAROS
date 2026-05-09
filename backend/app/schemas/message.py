from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from typing import Optional

class MessageCreate(BaseModel):
    job_id: UUID
    content: str = Field(..., min_length=1)
    image_url: Optional[str] = None

class MessageOut(BaseModel):
    id: UUID
    job_id: UUID
    sender_id: UUID
    content: str
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True