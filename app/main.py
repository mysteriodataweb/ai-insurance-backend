import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  (registers every table on Base.metadata)
from app.config import DEFAULT_SECRET_KEY, settings
from app.database import engine, Base
from app.errors import ConflictError, LLMError, NotFoundError
from app.routers import auth_router, claims_router, agent_router, dashboard_router, risk_router
from app.services.attachment_service import MAX_FILE_BYTES, MAX_FILES_PER_CLAIM

logging.basicConfig(level=logging.INFO)

MAX_UPLOAD_REQUEST_BYTES = MAX_FILE_BYTES * MAX_FILES_PER_CLAIM + 64 * 1024


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_production and settings.SECRET_KEY == DEFAULT_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production.")
    # Creates missing tables only; never drops or alters existing ones.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="AI Insurance Operations Platform",
    description="AI-powered insurance claims processing platform",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    # Reject oversized uploads before the multipart body is parsed and spooled to disk.
    if request.method == "POST" and request.url.path.endswith("/attachments"):
        length = request.headers.get("content-length", "")
        if length.isdigit() and int(length) > MAX_UPLOAD_REQUEST_BYTES:
            return JSONResponse({"detail": "Upload is too large."}, status_code=413)
    return await call_next(request)


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError):
    return JSONResponse({"detail": str(exc)}, status_code=404)


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError):
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.exception_handler(LLMError)
async def llm_error_handler(_request: Request, exc: LLMError):
    return JSONResponse({"detail": str(exc)}, status_code=502)


app.include_router(auth_router)
app.include_router(claims_router)
app.include_router(agent_router)
app.include_router(risk_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {"message": "AI Insurance Operations Platform API", "docs": "/docs"}
