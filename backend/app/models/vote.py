import uuid
import enum
from sqlalchemy import Column, String, Enum as SqlEnum, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base

class VoteOption(str, enum.Enum):
    FOR_CLIENT = "for_client"
    FOR_PROVIDER = "for_provider"

class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id = Column(UUID(as_uuid=True), ForeignKey("disputes.id"), nullable=False)
    juror_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    vote = Column(SqlEnum(VoteOption), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dispute = relationship("Dispute", back_populates="votes")
    juror = relationship("User")