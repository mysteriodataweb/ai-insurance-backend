from uuid import UUID
from pydantic import BaseModel

from app.schemas.common import UTCDateTime


class AttachmentResponse(BaseModel):
    id: UUID
    claim_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    created_at: UTCDateTime

    model_config = {"from_attributes": True}
