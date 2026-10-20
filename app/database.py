from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

# Tests run each case in its own event loop, so pooled asyncpg connections can't be reused there.
_engine_kwargs = {"poolclass": NullPool} if settings.APP_ENV == "test" else {"pool_pre_ping": True}
engine = create_async_engine(settings.DATABASE_URL, echo=settings.APP_DEBUG, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
