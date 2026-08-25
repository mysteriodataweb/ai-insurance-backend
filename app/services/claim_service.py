from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.audit_log import AuditLog
from app.schemas.claim import ClaimCreate


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


async def update_claim_status(db: AsyncSession, claim: Claim, new_status: str) -> Claim:
    claim.status = new_status
    await db.commit()
    await db.refresh(claim)
    return claim


async def get_claims_stats(db: AsyncSession) -> dict:
    total = await db.execute(select(func.count(Claim.id)))
    by_status = await db.execute(
        select(Claim.status, func.count(Claim.id)).group_by(Claim.status)
    )
    by_risk = await db.execute(
        select(Claim.risk_level, func.count(Claim.id)).group_by(Claim.risk_level)
    )
    return {
        "total": total.scalar(),
        "by_status": {row[0]: row[1] for row in by_status.all()},
        "by_risk": {row[0]: row[1] for row in by_risk.all()},
    }
