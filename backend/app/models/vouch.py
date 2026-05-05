import uuid
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


class Vouch(Base):
    __tablename__ = "vouches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    voucher_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # who gave the vouch (client)
    vouchee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # who received (provider)
    cnf_nft_id = Column(String(255), nullable=False)  # Underdog asset ID
    transaction_signature = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="vouches")
    voucher = relationship("User", back_populates="vouches_given", foreign_keys=[voucher_id])
    vouchee = relationship("User", back_populates="vouches_received", foreign_keys=[vouchee_id])