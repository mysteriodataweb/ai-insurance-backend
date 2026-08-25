from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ConversationMessage(BaseModel):
    id: UUID
    role: str
    message: str
    message_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerResponseRequest(BaseModel):
    message: str
