from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import UTCDateTime


class ConversationMessage(BaseModel):
    id: UUID
    role: str
    message: str
    message_type: str
    created_at: UTCDateTime

    model_config = {"from_attributes": True}


class CustomerResponseRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=5000)
