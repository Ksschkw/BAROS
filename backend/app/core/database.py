from sqlalchemy import text   # <-- add this
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Convert postgresql:// to postgresql+asyncpg://
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql+asyncpg://"):
    pass
else:
    raise ValueError("Invalid DATABASE_URL scheme. Expected postgresql:// or postgresql+asyncpg://")

engine = create_async_engine(database_url, echo=False, future=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass

async def init_db() -> None:
    """
    Create all tables that don't yet exist. This is safe to run on every startup.
    It will NOT drop or modify existing tables.
    """
    async with engine.begin() as conn:
        # Create tables (checkfirst=True avoids trying to create existing ones)
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        # Activate PostGIS extension if needed
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))