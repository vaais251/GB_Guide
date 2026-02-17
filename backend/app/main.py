"""
GB Guide — FastAPI Application Entry Point

Configures CORS, registers routers, and wires up lifecycle events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.routers.health import router as health_router


# ── Lifecycle ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    # Startup: create tables (dev only — use Alembic in prod)
    await create_db_and_tables()
    yield
    # Shutdown: add cleanup here if needed


# ── App Instance ────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Backend API for GB Guide — serves Web & Mobile clients.",
    lifespan=lifespan,
)


# ── CORS Middleware ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["*"],   # '*' for dev ease
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ─────────────────────────────────────────────────────
app.include_router(health_router)


# ── Root Redirect (optional convenience) ────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/api/health",
    }
