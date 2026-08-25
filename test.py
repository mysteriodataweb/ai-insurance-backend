import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import async_session, engine, Base
from app.models import Claim
from app.services import risk_engine


async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(select(Claim).limit(1))
        claim = result.scalar_one_or_none()

        if claim:
            print(f"Test claim: {claim.customer_name} - {claim.status}")
            assessment = await risk_engine.assess_risk(db, claim.id)
            print(f"Risk: {assessment.risk_score}/100 ({assessment.risk_level})")
            print(f"Signals: {assessment.signals}")
        else:
            print("No claims found. Run seed.py first.")

    print("Test completed successfully.")


if __name__ == "__main__":
    asyncio.run(test())
