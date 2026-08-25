import json
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openai import AsyncOpenAI
from app.config import settings
from app.models.claim import Claim
from app.models.extraction import ClaimExtraction
from app.models.conversation import Conversation
from app.services.claim_service import update_claim_status

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def run_extraction(db: AsyncSession, claim_id: UUID) -> ClaimExtraction:
    claim = await db.get(Claim, claim_id)

    from app.services.ai_extraction import extract_claim_info
    result = await extract_claim_info(claim.raw_description)

    extraction = ClaimExtraction(
        claim_id=claim_id,
        extracted_data=result.get("extracted_data", {}),
        missing_fields=result.get("missing_fields", []),
        confidence_scores=result.get("confidence_scores", {}),
        extraction_raw=result,
    )
    db.add(extraction)
    await update_claim_status(db, claim, "follow_up" if result.get("missing_fields") else "ready_for_review")
    await db.commit()
    await db.refresh(extraction)
    return extraction


async def generate_follow_up_questions(db: AsyncSession, claim_id: UUID) -> str:
    claim = await db.get(Claim, claim_id)
    extraction_result = await db.execute(
        select(ClaimExtraction).where(ClaimExtraction.claim_id == claim_id)
    )
    extraction = extraction_result.scalar_one_or_none()

    if not extraction or not extraction.missing_fields:
        return "All required information has been collected."

    missing = ", ".join(extraction.missing_fields)
    prompt = f"""You are an insurance claims agent. The customer submitted a claim but some information is missing.

Missing fields: {missing}
Original claim: "{claim.raw_description}"

Generate 1-3 specific, polite follow-up questions to collect the missing information.
Return ONLY a JSON array of strings, e.g. ["Question 1?", "Question 2?"]
No markdown, no explanation."""

    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    questions = result if isinstance(result, list) else result.get("questions", [])

    for q in questions:
        msg = Conversation(
            claim_id=claim_id,
            role="agent",
            message=q,
            message_type="question",
        )
        db.add(msg)

    await db.commit()
    return questions


async def process_customer_response(db: AsyncSession, claim_id: UUID, response_text: str) -> dict:
    claim = await db.get(Claim, claim_id)

    customer_msg = Conversation(
        claim_id=claim_id,
        role="customer",
        message=response_text,
        message_type="answer",
    )
    db.add(customer_msg)

    extraction_result = await db.execute(
        select(ClaimExtraction).where(ClaimExtraction.claim_id == claim_id)
    )
    extraction = extraction_result.scalar_one_or_none()

    if extraction:
        prompt = f"""The customer provided additional information for their insurance claim.

Original extracted data: {json.dumps(extraction.extracted_data)}
Missing fields: {json.dumps(extraction.missing_fields)}
Customer response: "{response_text}"

Update the extracted data with any new information found in the customer's response.
Return a JSON object with:
- "updated_data": the complete updated extracted_data dict
- "still_missing": list of fields still missing (empty if all complete)

Respond ONLY with valid JSON, no markdown."""

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        update = json.loads(response.choices[0].message.content)
        extraction.extracted_data = update.get("updated_data", extraction.extracted_data)
        extraction.missing_fields = update.get("still_missing", [])

        if not extraction.missing_fields:
            await update_claim_status(db, claim, "ready_for_review")
        else:
            from app.services.audit_service import log_event
            await log_event(db, claim_id, "customer_responded", {"fields_still_missing": extraction.missing_fields}, "customer")

    await db.commit()
    return {"status": "updated", "still_missing": extraction.missing_fields if extraction else []}
