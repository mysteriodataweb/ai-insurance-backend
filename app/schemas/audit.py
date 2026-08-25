from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    claim_id: UUID
    event_type: str
    event_data: dict
    actor: str
    created_at: datetime

    model_config = {"from_attributes": True}
