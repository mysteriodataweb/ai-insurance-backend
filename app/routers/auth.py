from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.rate_limit import rate_limit
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import (
    DUMMY_PASSWORD_HASH, create_access_token, get_current_user, hash_password, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


async def _find_user(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    return result.scalar_one_or_none()


@router.post("/register", response_model=TokenResponse, status_code=201,
             dependencies=[Depends(rate_limit(5, 3600))])
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is disabled. Ask an administrator for an account.")
    if await _find_user(db, data.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        role=data.role,
        password_hash=await run_in_threadpool(hash_password, data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit(10, 300))])
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await _find_user(db, data.email)
    valid = await run_in_threadpool(verify_password, data.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or not valid or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
