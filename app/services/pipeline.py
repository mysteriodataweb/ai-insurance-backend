import logging
from uuid import UUID

from app.database import async_session
from app.errors import ConflictError, LLMError
from app.models.claim import Claim
from app.services.ai_agent import generate_follow_up_questions, run_extraction
from app.services.audit_service import log_event
from app.services.risk_engine import assess_risk

logger = logging.getLogger(__name__)


async def process_new_claim(claim_id: UUID) -> None:
    """Background triage of a new claim: extraction, risk scoring, follow-up questions if needed."""
    async with async_session() as db:
        claim = await db.get(Claim, claim_id)
        if claim is None:
            return
        try:
            extraction = await run_extraction(db, claim)
            await assess_risk(db, claim)
            if extraction.missing_fields:
                await generate_follow_up_questions(db, claim)
        except (LLMError, ConflictError) as exc:
            await _record_failure(db, claim_id, str(exc))
        except Exception:
            logger.exception("AI pipeline crashed for claim %s", claim_id)
            await _record_failure(db, claim_id, "Unexpected error during automatic processing.")


async def _record_failure(db, claim_id: UUID, message: str) -> None:
    await db.rollback()
    await log_event(db, claim_id, "ai_pipeline_failed", {"error": message}, "system")
    await db.commit()
