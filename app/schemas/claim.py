from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class ClaimCreate(BaseModel):
    customer_name: str
    customer_email: str
    raw_description: str
    policy_number: Optional[str] = None
    incident_type: Optional[str] = None
    incident_date: Optional[date] = None
    incident_location: Optional[str] = None
    estimated_amount: Optional[Decimal] = None


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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClaimListResponse(BaseModel):
    id: UUID
    customer_name: str
    incident_type: Optional[str]
    status: str
    risk_level: str
    estimated_amount: Optional[Decimal]
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimActionRequest(BaseModel):
    action: str  # approved, rejected, escalated, info_requested
    performed_by: str
    notes: Optional[str] = None
