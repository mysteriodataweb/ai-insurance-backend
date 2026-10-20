from typing import Optional
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.rate_limit import rate_limit
from app.schemas.attachment import AttachmentResponse
from app.schemas.audit import AuditLogResponse
from app.schemas.claim import (
    ClaimActionRequest, ClaimActionResponse, ClaimCreate, ClaimListResponse, ClaimResponse, ClaimStatus, RiskLevel,
)
from app.security import get_current_user
from app.services import attachment_service, audit_service, claim_service
from app.services.pipeline import process_new_claim

router = APIRouter(prefix="/api/claims", tags=["claims"])


# Public: customers submit claims without an account.
@router.post("", response_model=ClaimResponse, status_code=201, dependencies=[Depends(rate_limit(20, 3600))])
async def submit_claim(data: ClaimCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    claim = await claim_service.create_claim(db, data)
    if settings.AUTO_PROCESS_CLAIMS:
        background_tasks.add_task(process_new_claim, claim.id)
    return claim


@router.get("", response_model=list[ClaimListResponse])
async def list_claims(
    status: Optional[ClaimStatus] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    incident_type: Optional[str] = Query(None, max_length=100),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await claim_service.list_claims(db, status, risk_level, incident_type, limit, offset)


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(claim_id: UUID, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    return await claim_service.get_claim_or_404(db, claim_id)


@router.put("/{claim_id}/action")
async def claim_action(
    claim_id: UUID,
    data: ClaimActionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    claim = await claim_service.get_claim_or_404(db, claim_id)
    await claim_service.apply_action(db, claim, data.action, user, data.notes)
    return {"status": "ok", "new_status": claim.status}


@router.get("/{claim_id}/actions", response_model=list[ClaimActionResponse])
async def list_actions(claim_id: UUID, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    await claim_service.get_claim_or_404(db, claim_id)
    return await claim_service.list_actions(db, claim_id)


@router.get("/{claim_id}/audit", response_model=list[AuditLogResponse])
async def get_audit_trail(claim_id: UUID, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    await claim_service.get_claim_or_404(db, claim_id)
    return await audit_service.get_audit_logs(db, claim_id)


# Public: the claim id (a random UUID) acts as the upload capability, within a limited window.
@router.post("/{claim_id}/attachments", response_model=list[AttachmentResponse], status_code=201,
             dependencies=[Depends(rate_limit(30, 3600))])
async def upload_attachments(
    claim_id: UUID,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    claim = await claim_service.get_claim_or_404(db, claim_id)
    try:
        return await attachment_service.add_attachments(db, claim, files)
    except attachment_service.AttachmentRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/{claim_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(claim_id: UUID, db: AsyncSession = Depends(get_db), _user: User = Depends(get_current_user)):
    await claim_service.get_claim_or_404(db, claim_id)
    return await attachment_service.list_attachments(db, claim_id)


@router.get("/{claim_id}/attachments/{attachment_id}")
async def download_attachment(
    claim_id: UUID,
    attachment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    attachment = await attachment_service.get_attachment_with_data(db, claim_id, attachment_id)
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return Response(
        content=attachment.data,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(attachment.filename)}",
            "X-Content-Type-Options": "nosniff",
        },
    )
