from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class RiskAssessmentResponse(BaseModel):
    id: UUID
    claim_id: UUID
    risk_score: int
    risk_level: str
    signals: list
    explanation: str
    recommended_action: str
    created_at: datetime

    model_config = {"from_attributes": True}
