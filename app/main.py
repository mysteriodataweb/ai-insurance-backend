from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import claims_router, agent_router, dashboard_router, risk_router

app = FastAPI(
    title="AI Insurance Operations Platform",
    description="AI-powered insurance claims processing platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims_router)
app.include_router(agent_router)
app.include_router(risk_router)
app.include_router(dashboard_router)


@app.on_event("startup")
async def startup():
    pass


@app.get("/")
async def root():
    return {"message": "AI Insurance Operations Platform API", "docs": "/docs"}
