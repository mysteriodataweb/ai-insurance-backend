import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base
from app.timeutils import utcnow


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, unique=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(SAEnum("low", "medium", "high", name="risk_level_enum"), nullable=False)
    signals = Column(JSONB, nullable=False, default=list)
    explanation = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    claim = relationship("Claim", back_populates="risk_assessment")
