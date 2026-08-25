import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Date, DateTime, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_number = Column(String(50), nullable=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    raw_description = Column(Text, nullable=False)
    incident_type = Column(String(100), nullable=True)
    incident_date = Column(Date, nullable=True)
    incident_location = Column(String(255), nullable=True)
    estimated_amount = Column(Numeric(12, 2), nullable=True)
    status = Column(
        SAEnum("submitted", "extracting", "follow_up", "ready_for_review",
               "under_review", "approved", "rejected", "escalated",
               name="claim_status"),
        default="submitted",
        nullable=False,
    )
    risk_level = Column(
        SAEnum("unrated", "low", "medium", "high", name="risk_level"),
        default="unrated",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    extraction = relationship("ClaimExtraction", back_populates="claim", uselist=False)
    conversations = relationship("Conversation", back_populates="claim", order_by="Conversation.created_at")
    risk_assessment = relationship("RiskAssessment", back_populates="claim", uselist=False)
    actions = relationship("ClaimAction", back_populates="claim", order_by="ClaimAction.created_at.desc()")
    audit_logs = relationship("AuditLog", back_populates="claim", order_by="AuditLog.created_at.desc()")
