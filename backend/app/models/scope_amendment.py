import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


class ScopeAmendment(Base):
    __tablename__ = "scope_amendments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    proposed_by = Column(String(50), nullable=False)  # "client" or "provider"
    reason = Column(Text, nullable=False)
    additional_cost = Column(Numeric(10, 2), nullable=True)
    new_total_price = Column(Numeric(10, 2), nullable=False)
    is_accepted = Column(Boolean, nullable=True)  # None = pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="scope_amendments")