import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, deferred

from app.database import Base
from app.timeutils import utcnow


class ClaimAttachment(Base):
    __tablename__ = "claim_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    # Deferred so listing attachments never loads file contents.
    data = deferred(Column(LargeBinary, nullable=False))
    created_at = Column(DateTime, default=utcnow, nullable=False)

    claim = relationship("Claim", back_populates="attachments")
