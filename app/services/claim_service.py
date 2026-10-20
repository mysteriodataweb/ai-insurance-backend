from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.models.audit_log import AuditLog, ClaimAction
from app.models.claim import Claim
from app.models.risk_assessment import RiskAssessment
from app.models.user import User
from app.schemas.claim import ClaimCreate

CLOSED_STATUSES = {"approved", "rejected"}

# Human decisions and the claim statuses they can be taken from.
ACTION_ALLOWED_FROM = {
    "approved": {"ready_for_review", "under_review", "escalated"},
    "rejected": {"follow_up", "ready_for_review", "under_review", "escalated"},
    "escalated": {"follow_up", "ready_for_review", "under_review"},
    "info_requested": {"ready_for_review", "under_review", "escalated"},
}
ACTION_NEW_STATUS = {
    "approved": "approved",
    "rejected": "rejected",
    "escalated": "escalated",
    "info_requested": "follow_up",
}


def ensure_open(claim: Claim) -> None:
    if claim.status in CLOSED_STATUSES:
        raise ConflictError(f"Claim is already {claim.status}.")


async def create_claim(db: AsyncSession, data: ClaimCreate) -> Claim:
    claim = Claim(**data.model_dump())
    db.add(claim)
    await db.flush()

    audit = AuditLog(
        claim_id=claim.id,
        event_type="claim_submitted",
        event_data={"customer_name": data.customer_name},
        actor="customer",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(claim)
    return claim


async def get_claim(db: AsyncSession, claim_id: UUID) -> Claim | None:
    result = await db.execute(select(Claim).where(Claim.id == claim_id))
    return result.scalar_one_or_none()


async def get_claim_or_404(db: AsyncSession, claim_id: UUID) -> Claim:
    claim = await get_claim(db, claim_id)
    if claim is None:
        raise NotFoundError("Claim not found")
    return claim


async def list_claims(
    db: AsyncSession,
    status: str | None = None,
    risk_level: str | None = None,
    incident_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Claim]:
    query = select(Claim)
    if status:
        query = query.where(Claim.status == status)
    if risk_level:
        query = query.where(Claim.risk_level == risk_level)
    if incident_type:
        query = query.where(Claim.incident_type == incident_type)
    query = query.order_by(Claim.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_actions(db: AsyncSession, claim_id: UUID) -> list[ClaimAction]:
    result = await db.execute(
        select(ClaimAction).where(ClaimAction.claim_id == claim_id).order_by(ClaimAction.created_at.desc())
    )
    return list(result.scalars().all())


async def apply_action(db: AsyncSession, claim: Claim, action: str, user: User, notes: str | None) -> ClaimAction:
    """Records a human decision, enforcing the review workflow and the four-eyes rule for high risk."""
    if claim.status not in ACTION_ALLOWED_FROM[action]:
        raise ConflictError(f"Cannot apply '{action}' to a claim with status '{claim.status}'.")

    if action == "rejected" and not notes:
        raise ConflictError("A note explaining the rejection is required.")

    if action == "approved":
        assessment = (await db.execute(
            select(RiskAssessment).where(RiskAssessment.claim_id == claim.id)
        )).scalar_one_or_none()
        if assessment is None:
            raise ConflictError("Run a risk assessment before approving this claim.")
        if claim.risk_level == "high":
            if claim.status != "escalated":
                raise ConflictError("High-risk claims must be escalated before they can be approved.")
            if not notes:
                raise ConflictError("A written justification is required to approve a high-risk claim.")
            escalation = next((a for a in await list_actions(db, claim.id) if a.action == "escalated"), None)
            if escalation is not None and escalation.performed_by == user.email:
                raise ConflictError("Four-eyes rule: a high-risk claim must be approved by someone other than the person who escalated it.")

    record = ClaimAction(claim_id=claim.id, action=action, performed_by=user.email, notes=notes)
    db.add(record)
    previous_status = claim.status
    claim.status = ACTION_NEW_STATUS[action]

    db.add(AuditLog(
        claim_id=claim.id,
        event_type=f"claim_{action}",
        event_data={"performed_by": user.email, "notes": notes, "previous_status": previous_status},
        actor="ops_agent",
    ))
    await db.commit()
    await db.refresh(claim)
    return record
