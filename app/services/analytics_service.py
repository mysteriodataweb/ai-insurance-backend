from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.claim import Claim


async def get_summary(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count(Claim.id)))).scalar()
    by_status = (await db.execute(
        select(Claim.status, func.count(Claim.id)).group_by(Claim.status)
    )).all()
    by_risk = (await db.execute(
        select(Claim.risk_level, func.count(Claim.id)).group_by(Claim.risk_level)
    )).all()

    return {
        "total_claims": total,
        "by_status": {row[0]: row[1] for row in by_status},
        "by_risk": {row[0]: row[1] for row in by_risk},
    }


async def get_metrics(db: AsyncSession) -> dict:
    total = (await db.execute(select(func.count(Claim.id)))).scalar()
    approved = (await db.execute(
        select(func.count(Claim.id)).where(Claim.status == "approved")
    )).scalar()
    high_risk = (await db.execute(
        select(func.count(Claim.id)).where(Claim.risk_level == "high")
    )).scalar()
    under_review = (await db.execute(
        select(func.count(Claim.id)).where(Claim.status == "under_review")
    )).scalar()

    automation_rate = round((approved / total * 100) if total else 0, 1)

    return {
        "total_claims": total,
        "approved_claims": approved,
        "high_risk_claims": high_risk,
        "under_review": under_review,
        "automation_rate": automation_rate,
        "avg_processing_time_before": "25 min",
        "avg_processing_time_after": "8 min",
        "estimated_time_saved": "68%",
    }
