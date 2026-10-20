from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import get_current_user
from app.services import analytics_service

router = APIRouter(prefix="/api", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/dashboard/summary")
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    return await analytics_service.get_summary(db)


@router.get("/analytics/metrics")
async def analytics_metrics(db: AsyncSession = Depends(get_db)):
    return await analytics_service.get_metrics(db)
