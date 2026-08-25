import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.risk_assessment import RiskAssessment
from app.models.extraction import ClaimExtraction
from app.services.claim_service import update_claim_status
from app.services.audit_service import log_event


def calculate_rule_based_score(claim: Claim, extraction: ClaimExtraction | None) -> tuple[int, list[str]]:
    score = 0
    signals = []

    if claim.estimated_amount and claim.estimated_amount > 10000:
        score += 25
        signals.append("Claim amount significantly above average ($10,000+)")

    if claim.estimated_amount and float(claim.estimated_amount) % 1000 == 0 and float(claim.estimated_amount) > 0:
        score += 5
        signals.append("Round claim amount (potential indicator)")

    if extraction and extraction.missing_fields:
        missing_count = len(extraction.missing_fields)
        if missing_count >= 2:
            score += 15
            signals.append(f"Multiple missing fields ({missing_count} fields)")
        elif missing_count == 1:
            score += 10
            signals.append("Missing supporting documentation")

    if extraction and extraction.confidence_scores:
        low_confidence = [k for k, v in extraction.confidence_scores.items() if v < 0.5]
        if low_confidence:
            score += 10
            signals.append(f"Low confidence on fields: {', '.join(low_confidence)}")

    if claim.incident_date:
        from datetime import datetime, timedelta
        days_since = (datetime.utcnow().date() - claim.incident_date).days
        if days_since > 30:
            score += 10
            signals.append(f"Late reporting ({days_since} days after incident)")

    return min(score, 100), signals


def get_risk_level(score: int) -> str:
    if score <= 30:
        return "low"
    elif score <= 70:
        return "medium"
    return "high"


def get_recommended_action(level: str, signals: list[str]) -> str:
    if level == "low":
        return "Standard processing. No manual review required."
    elif level == "medium":
        return "Manual review recommended. Check signals before approving."
    return "Manual investigation required. Multiple risk signals detected."


async def assess_risk(db: AsyncSession, claim_id: UUID) -> RiskAssessment:
    claim = await db.get(Claim, claim_id)

    from sqlalchemy import select
    extraction_result = await db.execute(
        select(ClaimExtraction).where(ClaimExtraction.claim_id == claim_id)
    )
    extraction = extraction_result.scalar_one_or_none()

    score, signals = calculate_rule_based_score(claim, extraction)
    level = get_risk_level(score)
    action = get_recommended_action(level, signals)

    explanation = f"Risk score: {score}/100 ({level}). "
    if signals:
        explanation += "Signals: " + "; ".join(signals) + ". "
    explanation += f"Recommended action: {action}"

    assessment = RiskAssessment(
        claim_id=claim_id,
        risk_score=score,
        risk_level=level,
        signals=signals,
        explanation=explanation,
        recommended_action=action,
    )
    db.add(assessment)
    await update_claim_status(db, claim, "under_review")
    claim.risk_level = level
    await log_event(db, claim_id, "risk_assessed", {"score": score, "level": level}, "system")
    await db.commit()
    await db.refresh(assessment)
    return assessment
