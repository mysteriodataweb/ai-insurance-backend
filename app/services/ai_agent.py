import json
from datetime import date

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, LLMError
from app.models.claim import Claim
from app.models.conversation import Conversation
from app.models.extraction import ClaimExtraction
from app.prompts import CUSTOMER_RESPONSE_SYSTEM_PROMPT, FOLLOW_UP_SYSTEM_PROMPT, wrap_untrusted
from app.services.ai_extraction import ExtractedData, extract_claim_info
from app.services.audit_service import log_event
from app.services.claim_data import apply_extracted_to_claim, compute_missing_fields
from app.services.claim_service import ensure_open
from app.services.llm import complete_json
from app.timeutils import utcnow

# Statuses the AI pipeline may move a claim between; escalated/closed claims keep their status.
PIPELINE_STATUSES = {"submitted", "extracting", "follow_up", "ready_for_review", "under_review"}

TEMPLATE_QUESTIONS = {
    "incident_type": "What type of incident are you claiming for (e.g. car accident, theft, fire, water damage)?",
    "incident_date": "On what date did the incident happen?",
    "incident_location": "Where did the incident take place (city and address if possible)?",
    "estimated_amount": "What is the estimated amount of the loss or repair, in dollars?",
    "damage_description": "Could you describe the damage or loss in more detail?",
    "policy_number": "Could you provide your insurance policy number?",
}


async def get_extraction(db: AsyncSession, claim_id) -> ClaimExtraction | None:
    result = await db.execute(select(ClaimExtraction).where(ClaimExtraction.claim_id == claim_id))
    return result.scalar_one_or_none()


async def run_extraction(db: AsyncSession, claim: Claim) -> ClaimExtraction:
    ensure_open(claim)
    result, raw = await extract_claim_info(claim.raw_description, today=date.today())
    extracted = result.extracted_data.model_dump(mode="json")

    filled = apply_extracted_to_claim(claim, extracted)
    missing = compute_missing_fields(claim, extracted)

    extraction = await get_extraction(db, claim.id)
    rerun = extraction is not None
    if extraction is None:
        extraction = ClaimExtraction(claim_id=claim.id)
        db.add(extraction)
    extraction.extracted_data = extracted
    extraction.missing_fields = missing
    extraction.confidence_scores = result.confidence_scores
    extraction.extraction_raw = raw
    extraction.created_at = utcnow()

    if claim.status in PIPELINE_STATUSES:
        claim.status = "follow_up" if missing else "ready_for_review"

    await log_event(db, claim.id, "ai_extraction_completed", {
        "missing_fields": missing,
        "autofilled_fields": filled,
        "rerun": rerun,
    }, "ai_agent")
    await db.commit()
    await db.refresh(extraction)
    return extraction


def _parse_questions(raw: dict) -> list[str]:
    questions = raw.get("questions")
    if not isinstance(questions, list):
        raise LLMError("AI follow-up did not return a 'questions' list.")
    cleaned = [str(q).strip()[:300] for q in questions if isinstance(q, (str, int, float)) and str(q).strip()]
    if not cleaned:
        raise LLMError("AI follow-up returned no questions.")
    return cleaned[:3]


async def generate_follow_up_questions(db: AsyncSession, claim: Claim) -> list[str]:
    """Returns the questions asked (empty when nothing is missing). Falls back to templates if the AI fails."""
    ensure_open(claim)
    extraction = await get_extraction(db, claim.id)
    if extraction is None:
        raise ConflictError("Run the AI extraction before generating follow-up questions.")
    missing = list(extraction.missing_fields or [])
    if not missing:
        return []

    source = "ai"
    try:
        raw = await complete_json(
            FOLLOW_UP_SYSTEM_PROMPT,
            f"Missing fields: {', '.join(missing)}\n\n" + wrap_untrusted("claim_description", claim.raw_description),
            temperature=0.3,
        )
        questions = _parse_questions(raw)
    except LLMError:
        source = "template"
        questions = [TEMPLATE_QUESTIONS.get(f, f"Could you provide the {f.replace('_', ' ')}?") for f in missing][:3]

    for q in questions:
        db.add(Conversation(claim_id=claim.id, role="agent", message=q, message_type="question"))
    await log_event(db, claim.id, "follow_up_generated", {"questions_count": len(questions), "source": source}, "ai_agent")
    await db.commit()
    return questions


async def process_customer_response(db: AsyncSession, claim: Claim, response_text: str) -> dict:
    """Records a customer's reply and merges any new facts into the extraction. All-or-nothing."""
    ensure_open(claim)
    extraction = await get_extraction(db, claim.id)
    if extraction is None:
        raise ConflictError("Run the AI extraction before recording customer responses.")

    current = dict(extraction.extracted_data or {})
    raw = await complete_json(
        CUSTOMER_RESPONSE_SYSTEM_PROMPT,
        f"Current claim data: {json.dumps(current)}\n"
        f"Missing fields: {json.dumps(list(extraction.missing_fields or []))}\n\n"
        + wrap_untrusted("customer_reply", response_text),
        temperature=0.1,
    )
    update = raw.get("updated_data")
    if not isinstance(update, dict):
        raise LLMError("AI did not return 'updated_data'.")
    try:
        parsed = ExtractedData.model_validate(update).model_dump(mode="json")
    except ValidationError as exc:
        raise LLMError("AI returned malformed claim data.") from exc
    provided = {k: v for k, v in parsed.items() if k in update and v is not None}

    merged = {**current, **provided}
    db.add(Conversation(claim_id=claim.id, role="customer", message=response_text, message_type="answer"))
    filled = apply_extracted_to_claim(claim, merged)
    missing = compute_missing_fields(claim, merged)
    extraction.extracted_data = merged
    extraction.missing_fields = missing
    # Facts the customer stated directly are no longer AI guesses.
    extraction.confidence_scores = {**(extraction.confidence_scores or {}), **{field: 1.0 for field in provided}}
    if not missing and claim.status == "follow_up":
        claim.status = "ready_for_review"

    await log_event(db, claim.id, "customer_responded", {
        "updated_fields": sorted(provided),
        "autofilled_fields": filled,
        "still_missing": missing,
    }, "customer")
    await db.commit()
    return {"status": claim.status, "still_missing": missing}
