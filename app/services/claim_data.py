"""Deterministic merge of customer-declared claim data and AI-extracted data."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.claim import Claim

# Fields a claim needs before it can be reviewed. Computed in code, not by the LLM,
# so a manipulated description can't talk its way out of the follow-up step.
REQUIRED_FIELDS = (
    "incident_type",
    "incident_date",
    "incident_location",
    "estimated_amount",
    "damage_description",
    "policy_number",
)

# Extracted fields that also exist as columns on the claim, with their max length when textual.
CLAIM_COLUMNS = {
    "incident_type": 100,
    "incident_date": None,
    "incident_location": 255,
    "estimated_amount": None,
    "policy_number": 50,
}


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _to_column_value(field: str, value: Any) -> Any:
    if field == "incident_date":
        return value if isinstance(value, date) else date.fromisoformat(str(value))
    if field == "estimated_amount":
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
        if amount <= 0 or amount >= Decimal("10000000000"):
            raise ValueError("amount out of range")
        return amount
    return str(value)[: CLAIM_COLUMNS[field]]


def apply_extracted_to_claim(claim: Claim, extracted: dict) -> list[str]:
    """Fill empty claim columns with extracted values. Declared values always win. Returns filled fields."""
    filled = []
    for field in CLAIM_COLUMNS:
        value = extracted.get(field)
        if _is_empty(value) or not _is_empty(getattr(claim, field)):
            continue
        try:
            setattr(claim, field, _to_column_value(field, value))
        except (ValueError, InvalidOperation):
            continue
        filled.append(field)
    return filled


def compute_missing_fields(claim: Claim, extracted: dict) -> list[str]:
    missing = []
    for field in REQUIRED_FIELDS:
        declared = getattr(claim, field) if field in CLAIM_COLUMNS else None
        if _is_empty(declared) and _is_empty(extracted.get(field)):
            missing.append(field)
    return missing


def low_confidence_fields(extracted: dict, confidence_scores: dict, threshold: float = 0.5) -> list[str]:
    """Fields the AI did extract but is unsure about."""
    return sorted(
        field for field, score in confidence_scores.items()
        if not _is_empty(extracted.get(field)) and isinstance(score, (int, float)) and score < threshold
    )
