"""
GB Guide — Database Engine & Session

Uses async SQLAlchemy with asyncpg driver.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import settings
import app.models  # noqa: F401  — registers all tables with SQLModel.metadata

# ── Engine ──────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    future=True,
)

# ── Session Factory ─────────────────────────────────────────────
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Dependency ──────────────────────────────────────────────────
async def get_session() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency that yields a DB session."""
    async with async_session() as session:
        yield session


# ── Table Creation (dev convenience) ────────────────────────────
async def create_db_and_tables() -> None:
    """Create all SQLModel tables. Use Alembic in production."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
