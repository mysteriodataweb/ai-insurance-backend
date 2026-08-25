from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimListResponse, ClaimActionRequest
from app.schemas.extraction import ExtractionResponse
from app.services import claim_service, ai_agent, audit_service
from app.models.audit_log import ClaimAction

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.post("", response_model=ClaimResponse, status_code=201)
async def submit_claim(data: ClaimCreate, db: AsyncSession = Depends(get_db)):
    claim = await claim_service.create_claim(db, data)
    return claim


@router.get("", response_model=list[ClaimListResponse])
async def list_claims(
    status: str | None = Query(None),
    risk_level: str | None = Query(None),
    incident_type: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await claim_service.list_claims(db, status, risk_level, incident_type, limit, offset)


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    claim = await claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim


@router.put("/{claim_id}/action")
async def claim_action(claim_id: UUID, data: ClaimActionRequest, db: AsyncSession = Depends(get_db)):
    claim = await claim_service.get_claim(db, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    action = ClaimAction(
        claim_id=claim_id,
        action=data.action,
        performed_by=data.performed_by,
        notes=data.notes,
    )
    db.add(action)

    status_map = {
        "approved": "approved",
        "rejected": "rejected",
        "escalated": "escalated",
        "info_requested": "follow_up",
    }
    new_status = status_map.get(data.action)
    if new_status:
        await claim_service.update_claim_status(db, claim, new_status)

    await audit_service.log_event(
        db, claim_id, f"claim_{data.action}", {"performed_by": data.performed_by, "notes": data.notes}, "ops_agent"
    )
    await db.commit()
    return {"status": "ok", "new_status": claim.status}
