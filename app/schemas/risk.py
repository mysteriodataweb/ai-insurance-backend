from uuid import UUID
from pydantic import BaseModel

from app.schemas.common import UTCDateTime


class RiskAssessmentResponse(BaseModel):
    id: UUID
    claim_id: UUID
    risk_score: int
    risk_level: str
    signals: list
    explanation: str
    recommended_action: str
    created_at: UTCDateTime

    model_config = {"from_attributes": True}
