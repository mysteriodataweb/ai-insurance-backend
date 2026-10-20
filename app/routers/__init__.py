from app.routers.auth import router as auth_router
from app.routers.claims import router as claims_router
from app.routers.agent import router as agent_router
from app.routers.dashboard import router as dashboard_router
from app.routers.risk import router as risk_router

__all__ = ["auth_router", "claims_router", "agent_router", "dashboard_router", "risk_router"]
