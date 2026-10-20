from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.risk_assessment import RiskAssessment
from app.schemas.risk import RiskAssessmentResponse
from app.security import get_current_user
from app.services import risk_engine
from app.services.claim_service import get_claim_or_404

router = APIRouter(prefix="/api/risk", tags=["risk"], dependencies=[Depends(get_current_user)])


@router.post("/assess/{claim_id}", response_model=RiskAssessmentResponse)
async def assess_risk(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    claim = await get_claim_or_404(db, claim_id)
    return await risk_engine.assess_risk(db, claim)


@router.get("/{claim_id}", response_model=RiskAssessmentResponse)
async def get_risk(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RiskAssessment).where(RiskAssessment.claim_id == claim_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    return assessment
