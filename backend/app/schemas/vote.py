from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from ..models.vote import VoteOption

class VoteCreate(BaseModel):
    dispute_id: UUID
    vote: VoteOption

class VoteOut(BaseModel):
    id: UUID
    dispute_id: UUID
    juror_id: UUID
    vote: VoteOption
    created_at: datetime

    class Config:
        from_attributes = True