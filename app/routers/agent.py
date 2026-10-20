from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation
from app.rate_limit import rate_limit
from app.schemas.conversation import ConversationMessage, CustomerResponseRequest
from app.schemas.extraction import ExtractionResponse
from app.security import get_current_user
from app.services import ai_agent
from app.services.claim_service import get_claim_or_404

router = APIRouter(prefix="/api/agent", tags=["agent"], dependencies=[Depends(get_current_user)])

# Calls that hit the paid/quota-limited AI provider.
ai_rate_limit = rate_limit(30, 600)


@router.post("/extract/{claim_id}", response_model=ExtractionResponse, dependencies=[Depends(ai_rate_limit)])
async def extract_claim(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    claim = await get_claim_or_404(db, claim_id)
    return await ai_agent.run_extraction(db, claim)


@router.get("/extraction/{claim_id}", response_model=ExtractionResponse)
async def get_extraction(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    extraction = await ai_agent.get_extraction(db, claim_id)
    if extraction is None:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return extraction


@router.get("/conversation/{claim_id}", response_model=list[ConversationMessage])
async def get_conversation(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.claim_id == claim_id).order_by(Conversation.created_at)
    )
    return list(result.scalars().all())


@router.post("/follow-up/{claim_id}", dependencies=[Depends(ai_rate_limit)])
async def trigger_follow_up(claim_id: UUID, db: AsyncSession = Depends(get_db)):
    claim = await get_claim_or_404(db, claim_id)
    questions = await ai_agent.generate_follow_up_questions(db, claim)
    return {"questions": questions}


@router.post("/respond/{claim_id}", dependencies=[Depends(ai_rate_limit)])
async def customer_respond(claim_id: UUID, data: CustomerResponseRequest, db: AsyncSession = Depends(get_db)):
    claim = await get_claim_or_404(db, claim_id)
    return await ai_agent.process_customer_response(db, claim, data.message)
