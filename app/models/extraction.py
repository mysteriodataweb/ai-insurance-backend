import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ClaimExtraction(Base):
    __tablename__ = "claim_extractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, unique=True)
    extracted_data = Column(JSONB, nullable=False, default=dict)
    missing_fields = Column(JSONB, nullable=False, default=list)
    confidence_scores = Column(JSONB, nullable=False, default=dict)
    extraction_raw = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    claim = relationship("Claim", back_populates="extraction")
