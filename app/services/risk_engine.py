from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError
from app.models.claim import Claim
from app.models.extraction import ClaimExtraction
from app.models.risk_assessment import RiskAssessment
from app.services.audit_service import log_event
from app.services.claim_data import compute_missing_fields, low_confidence_fields
from app.services.claim_service import ensure_open
from app.timeutils import utcnow

LOW_MAX = 30
MEDIUM_MAX = 70


@dataclass(frozen=True)
class RiskInputs:
    declared_amount: float | None
    extracted_amount: float | None
    incident_date: date | None
    missing_fields: list[str]
    low_confidence_fields: list[str]
    prior_claims_count: int
    today: date


def _as_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def calculate_risk(inputs: RiskInputs) -> tuple[int, list[str]]:
    """Deterministic, explainable score: each signal adds points and a human-readable reason."""
    score = 0
    signals = []

    def add(points: int, reason: str):
        nonlocal score
        score += points
        signals.append(f"{reason} (+{points})")

    amount = inputs.declared_amount if inputs.declared_amount is not None else inputs.extracted_amount
    if amount is not None:
        if amount > 25_000:
            add(45, "Very high claim amount (above $25,000)")
        elif amount > 10_000:
            add(30, "High claim amount (above $10,000)")
        if amount >= 1_000 and amount % 1_000 == 0:
            add(5, "Round claim amount")

    if inputs.declared_amount and inputs.extracted_amount:
        gap = abs(inputs.declared_amount - inputs.extracted_amount) / max(inputs.declared_amount, inputs.extracted_amount)
        if gap > 0.2:
            add(20, f"Declared amount (${inputs.declared_amount:,.0f}) differs from the description (${inputs.extracted_amount:,.0f})")

    missing = len(inputs.missing_fields)
    if missing >= 2:
        add(20, f"Multiple missing fields: {', '.join(inputs.missing_fields)}")
    elif missing == 1:
        add(10, f"Missing field: {inputs.missing_fields[0]}")

    if inputs.low_confidence_fields:
        add(10, f"Low AI confidence on: {', '.join(inputs.low_confidence_fields)}")

    if inputs.incident_date:
        days_since = (inputs.today - inputs.incident_date).days
        if days_since < -1:
            add(20, "Incident date is in the future")
        elif days_since > 90:
            add(25, f"Very late reporting ({days_since} days after incident)")
        elif days_since > 30:
            add(15, f"Late reporting ({days_since} days after incident)")

    if inputs.prior_claims_count >= 2:
        add(15, f"Customer filed {inputs.prior_claims_count} other claims in the last 12 months")
    elif inputs.prior_claims_count == 1:
        add(5, "Customer filed another claim in the last 12 months")

    return min(score, 100), signals


def get_risk_level(score: int) -> str:
    if score <= LOW_MAX:
        return "low"
    elif score <= MEDIUM_MAX:
        return "medium"
    return "high"


def get_recommended_action(level: str) -> str:
    if level == "low":
        return "Standard processing. Eligible for fast-track approval after a quick check."
    elif level == "medium":
        return "Manual review recommended. Check signals before approving."
    return "Manual investigation required. Escalate; approval needs a second reviewer and a written justification."


async def _count_prior_claims(db: AsyncSession, claim: Claim) -> int:
    since = utcnow() - timedelta(days=365)
    result = await db.execute(
        select(func.count(Claim.id)).where(
            func.lower(Claim.customer_email) == claim.customer_email.lower(),
            Claim.id != claim.id,
            Claim.created_at >= since,
        )
    )
    return result.scalar() or 0


async def assess_risk(db: AsyncSession, claim: Claim) -> RiskAssessment:
    ensure_open(claim)
    extraction = (await db.execute(
        select(ClaimExtraction).where(ClaimExtraction.claim_id == claim.id)
    )).scalar_one_or_none()
    if extraction is None:
        raise ConflictError("Run the AI extraction before assessing risk.")

    extracted = extraction.extracted_data or {}
    inputs = RiskInputs(
        declared_amount=float(claim.estimated_amount) if claim.estimated_amount is not None else None,
        extracted_amount=_as_float(extracted.get("estimated_amount")),
        incident_date=claim.incident_date,
        missing_fields=compute_missing_fields(claim, extracted),
        low_confidence_fields=low_confidence_fields(extracted, extraction.confidence_scores or {}),
        prior_claims_count=await _count_prior_claims(db, claim),
        today=date.today(),
    )
    score, signals = calculate_risk(inputs)
    level = get_risk_level(score)
    action = get_recommended_action(level)

    explanation = f"Risk score: {score}/100 ({level}). "
    explanation += ("Signals: " + "; ".join(signals) + ". ") if signals else "No risk signals detected. "
    explanation += f"Recommended action: {action}"

    assessment = (await db.execute(
        select(RiskAssessment).where(RiskAssessment.claim_id == claim.id)
    )).scalar_one_or_none()
    rerun = assessment is not None
    if assessment is None:
        assessment = RiskAssessment(claim_id=claim.id)
        db.add(assessment)
    assessment.risk_score = score
    assessment.risk_level = level
    assessment.signals = signals
    assessment.explanation = explanation
    assessment.recommended_action = action
    assessment.created_at = utcnow()

    claim.risk_level = level
    if claim.status == "ready_for_review":
        claim.status = "under_review"

    await log_event(db, claim.id, "risk_assessed", {"score": score, "level": level, "rerun": rerun}, "system")
    await db.commit()
    await db.refresh(assessment)
    return assessment
