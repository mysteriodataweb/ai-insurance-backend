from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.schemas.common import UTCDateTime


class ExtractionResponse(BaseModel):
    id: UUID
    claim_id: UUID
    extracted_data: dict
    missing_fields: list
    confidence_scores: dict
    extraction_raw: Optional[dict]
    created_at: UTCDateTime

    model_config = {"from_attributes": True}
