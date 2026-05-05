from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class MessageCreate(BaseModel):
    job_id: UUID
    content: str = Field(..., min_length=1)

class MessageOut(BaseModel):
    id: UUID
    job_id: UUID
    sender_id: UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True