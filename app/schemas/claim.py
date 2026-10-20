from datetime import date, timedelta
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import UTCDateTime

ClaimStatus = Literal[
    "submitted", "extracting", "follow_up", "ready_for_review",
    "under_review", "approved", "rejected", "escalated",
]
RiskLevel = Literal["unrated", "low", "medium", "high"]
ClaimActionType = Literal["approved", "rejected", "escalated", "info_requested"]


class ClaimCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    customer_name: str = Field(min_length=1, max_length=255)
    customer_email: EmailStr
    raw_description: str = Field(min_length=20, max_length=5000)
    policy_number: Optional[str] = Field(None, max_length=50)
    incident_type: Optional[str] = Field(None, max_length=100)
    incident_date: Optional[date] = None
    incident_location: Optional[str] = Field(None, max_length=255)
    estimated_amount: Optional[Decimal] = Field(None, ge=0, le=Decimal("10000000"), decimal_places=2)

    @field_validator("policy_number", "incident_type", "incident_location", "incident_date", "estimated_amount", mode="before")
    @classmethod
    def empty_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("incident_date")
    @classmethod
    def not_in_future(cls, value: Optional[date]) -> Optional[date]:
        # One day of tolerance for customers ahead of UTC.
        if value and value > date.today() + timedelta(days=1):
            raise ValueError("incident date cannot be in the future")
        return value


class ClaimResponse(BaseModel):
    id: UUID
    customer_name: str
    customer_email: str
    raw_description: str
    policy_number: Optional[str]
    incident_type: Optional[str]
    incident_date: Optional[date]
    incident_location: Optional[str]
    estimated_amount: Optional[Decimal]
    status: str
    risk_level: str
    created_at: UTCDateTime
    updated_at: UTCDateTime

    model_config = {"from_attributes": True}


class ClaimListResponse(BaseModel):
    id: UUID
    customer_name: str
    incident_type: Optional[str]
    status: str
    risk_level: str
    estimated_amount: Optional[Decimal]
    created_at: UTCDateTime

    model_config = {"from_attributes": True}


class ClaimActionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    action: ClaimActionType
    notes: Optional[str] = Field(None, max_length=2000)


class ClaimActionResponse(BaseModel):
    id: UUID
    action: str
    performed_by: str
    notes: Optional[str]
    created_at: UTCDateTime

    model_config = {"from_attributes": True}
