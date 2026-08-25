from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.claim import Claim


async def log_event(
    db: AsyncSession,
    claim_id: UUID,
    event_type: str,
    event_data: dict,
    actor: str = "system",
) -> AuditLog:
    audit = AuditLog(
        claim_id=claim_id,
        event_type=event_type,
        event_data=event_data,
        actor=actor,
    )
    db.add(audit)
    await db.flush()
    return audit


async def get_audit_logs(db: AsyncSession, claim_id: UUID) -> list[AuditLog]:
    from sqlalchemy import select
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.claim_id == claim_id)
        .order_by(AuditLog.created_at.desc())
    )
    return list(result.scalars().all())
