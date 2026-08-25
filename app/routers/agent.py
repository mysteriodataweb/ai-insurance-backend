from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.conversation import Conversation
from app.models.extraction import ClaimExtraction
from app.schemas.extraction import ExtractionResponse
from app.schemas.conversation import ConversationMessage, CustomerResponseRequest
from app.services import ai_agent, audit_service

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/extract/{claim_id}", response_model=ExtractionResponse)
async def extract_claim(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    extraction = await ai_agent.run_extraction(db, claim_id)
    await audit_service.log_event(db, claim_id, "ai_extraction_completed", {"extraction_id": str(extraction.id)}, "ai_agent")
    return extraction


@router.get("/conversation/{claim_id}", response_model=list[ConversationMessage])
async def get_conversation(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.claim_id == claim_id).order_by(Conversation.created_at)
    )
    return list(result.scalars().all())


@router.post("/follow-up/{claim_id}")
async def trigger_follow_up(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    questions = await ai_agent.generate_follow_up_questions(db, claim_id)
    await audit_service.log_event(db, claim_id, "follow_up_generated", {"questions_count": len(questions)}, "ai_agent")
    return {"questions": questions}


@router.post("/respond/{claim_id}")
async def customer_respond(claim_id: UUID, data: CustomerResponseRequest, db: AsyncSession = Depends(get_db)):
    result = await ai_agent.process_customer_response(db, claim_id, data.message)
    return result
