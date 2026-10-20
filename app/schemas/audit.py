from uuid import UUID
from pydantic import BaseModel

from app.schemas.common import UTCDateTime


class AuditLogResponse(BaseModel):
    id: UUID
    claim_id: UUID
    event_type: str
    event_data: dict
    actor: str
    created_at: UTCDateTime

    model_config = {"from_attributes": True}
