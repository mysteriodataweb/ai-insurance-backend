from datetime import date, timedelta

from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import ClaimAction
from app.models.claim import Claim
from app.models.extraction import ClaimExtraction
from app.models.risk_assessment import RiskAssessment

REVIEW_STATUSES = ("ready_for_review", "under_review", "escalated")
DECIDED_STATUSES = ("approved", "rejected")


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


def _pct(part: int, whole: int) -> float | None:
    return round(part / whole * 100, 1) if whole else None


async def _count(db: AsyncSession, *conditions) -> int:
    return (await db.execute(select(func.count(Claim.id)).where(*conditions))).scalar() or 0


async def _avg_seconds(db: AsyncSession, query) -> float | None:
    seconds = (await db.execute(query)).scalar()
    return float(seconds) if seconds is not None else None


async def get_metrics(db: AsyncSession) -> dict:
    """Operational metrics computed from the database. Nothing here is simulated."""
    total = await _count(db)
    by_risk = dict((await db.execute(
        select(Claim.risk_level, func.count(Claim.id)).group_by(Claim.risk_level)
    )).all())
    by_type = (await db.execute(
        select(Claim.incident_type, func.count(Claim.id))
        .group_by(Claim.incident_type)
        .order_by(func.count(Claim.id).desc())
    )).all()

    ai_processed = (await db.execute(select(func.count(ClaimExtraction.id)))).scalar() or 0
    assessed = (await db.execute(select(func.count(RiskAssessment.id)))).scalar() or 0
    fast_track = await _count(db, Claim.risk_level == "low", Claim.status.in_(REVIEW_STATUSES))
    needs_review = (await db.execute(
        select(func.count(RiskAssessment.id)).where(RiskAssessment.risk_level.in_(("medium", "high")))
    )).scalar() or 0

    # Time from submission to the first human approve/reject decision.
    first_decision = (
        select(ClaimAction.claim_id, func.min(ClaimAction.created_at).label("decided_at"))
        .where(ClaimAction.action.in_(DECIDED_STATUSES))
        .group_by(ClaimAction.claim_id)
        .subquery()
    )
    decision_seconds = await _avg_seconds(db, select(
        func.avg(func.extract("epoch", first_decision.c.decided_at - Claim.created_at))
    ).select_from(Claim).join(first_decision, first_decision.c.claim_id == Claim.id))
    # Time from submission to the (latest) AI extraction.
    triage_seconds = await _avg_seconds(db, select(
        func.avg(func.extract("epoch", ClaimExtraction.created_at - Claim.created_at))
    ).select_from(Claim).join(ClaimExtraction, ClaimExtraction.claim_id == Claim.id))

    today = date.today()
    since_day = today - timedelta(days=13)
    per_day = dict((await db.execute(
        select(func.date(Claim.created_at), func.count(Claim.id))
        .where(func.date(Claim.created_at) >= since_day)
        .group_by(func.date(Claim.created_at))
    )).all())
    week_start = today - timedelta(days=today.weekday())
    since_week = week_start - timedelta(weeks=7)
    # Literal (not bound) 'week' so SELECT and GROUP BY are the same expression for Postgres.
    week_of = func.date(func.date_trunc(literal_column("'week'"), Claim.created_at))
    per_week = dict((await db.execute(
        select(week_of, func.count(Claim.id))
        .where(Claim.created_at >= since_week)
        .group_by(week_of)
    )).all())

    return {
        "total_claims": total,
        "approved_claims": await _count(db, Claim.status == "approved"),
        "rejected_claims": await _count(db, Claim.status == "rejected"),
        "high_risk_claims": by_risk.get("high", 0),
        "under_review": await _count(db, Claim.status.in_(REVIEW_STATUSES)),
        "awaiting_customer": await _count(db, Claim.status == "follow_up"),
        "ai_processed_claims": ai_processed,
        "ai_processed_rate": _pct(ai_processed, total),
        "assessed_claims": assessed,
        "fast_track_eligible": fast_track,
        "human_review_rate": _pct(needs_review, assessed),
        "avg_decision_hours": round(decision_seconds / 3600, 1) if decision_seconds is not None else None,
        "avg_triage_minutes": round(triage_seconds / 60, 1) if triage_seconds is not None else None,
        "by_risk": {level: by_risk.get(level, 0) for level in ("low", "medium", "high", "unrated")},
        "by_type": [{"name": name or "Unspecified", "count": count} for name, count in by_type],
        "claims_per_day": [
            {"date": (since_day + timedelta(days=i)).isoformat(), "count": per_day.get(since_day + timedelta(days=i), 0)}
            for i in range(14)
        ],
        "claims_per_week": [
            {"week_start": (since_week + timedelta(weeks=i)).isoformat(), "count": per_week.get(since_week + timedelta(weeks=i), 0)}
            for i in range(8)
        ],
    }
