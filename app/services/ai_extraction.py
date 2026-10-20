import re
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.errors import LLMError
from app.prompts import EXTRACTION_SYSTEM_PROMPT, wrap_untrusted
from app.services.llm import complete_json

EXTRACTION_FIELDS = (
    "incident_type",
    "incident_date",
    "incident_location",
    "estimated_amount",
    "damage_description",
    "other_party_info",
    "policy_number",
)

_NULL_STRINGS = {"", "null", "none", "n/a", "na", "unknown", "not provided", "not specified"}


class ExtractedData(BaseModel):
    """LLM output is coerced field by field: anything unusable becomes null instead of failing."""

    model_config = ConfigDict(extra="ignore")

    incident_type: Optional[str] = None
    incident_date: Optional[date] = None
    incident_location: Optional[str] = None
    estimated_amount: Optional[float] = None
    damage_description: Optional[str] = None
    other_party_info: Optional[str] = None
    policy_number: Optional[str] = None

    @field_validator("*", mode="before")
    @classmethod
    def null_like_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip().lower() in _NULL_STRINGS:
            return None
        return value

    @field_validator("incident_type", "incident_location", "damage_description", "other_party_info", "policy_number", mode="before")
    @classmethod
    def to_text(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return None
        return str(value).strip()[:500] or None

    @field_validator("incident_date", mode="before")
    @classmethod
    def to_date(cls, value: Any) -> Optional[date]:
        if value is None or isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value).strip()[:10])
        except ValueError:
            return None

    @field_validator("estimated_amount", mode="before")
    @classmethod
    def to_amount(cls, value: Any) -> Optional[float]:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, str):
            value = re.sub(r"[^\d.\-]", "", value)
        try:
            amount = float(value)
        except (TypeError, ValueError):
            return None
        return amount if 0 < amount < 1e10 else None


class ExtractionResult(BaseModel):
    extracted_data: ExtractedData
    confidence_scores: dict[str, float]


def _to_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(max(score, 0.0), 1.0)


def parse_extraction(raw: dict) -> ExtractionResult:
    data = raw.get("extracted_data")
    if not isinstance(data, dict):
        raise LLMError("AI extraction did not return 'extracted_data'.")
    try:
        extracted = ExtractedData.model_validate(data)
    except ValidationError as exc:
        raise LLMError("AI extraction returned malformed data.") from exc

    scores_raw = raw.get("confidence_scores")
    scores_raw = scores_raw if isinstance(scores_raw, dict) else {}
    values = extracted.model_dump()
    scores = {}
    for field in EXTRACTION_FIELDS:
        # A field the model could not extract carries no confidence, whatever it claims.
        scores[field] = _to_score(scores_raw.get(field)) if values[field] is not None else 0.0
    return ExtractionResult(extracted_data=extracted, confidence_scores=scores)


async def extract_claim_info(description: str, today: date) -> tuple[ExtractionResult, dict]:
    system_prompt = EXTRACTION_SYSTEM_PROMPT.replace("{today}", today.isoformat())
    raw = await complete_json(system_prompt, wrap_untrusted("claim_description", description), temperature=0.1)
    return parse_extraction(raw), raw
