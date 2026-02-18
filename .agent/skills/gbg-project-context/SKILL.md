---
name: gbg-project-context
description: GB Guide (GBG) — Full-stack project context, architecture, conventions, and how to run common tasks.
---

# GB Guide (GBG) — Project Skill

## Overview
GB Guide is a tourism platform for **Gilgit-Baltistan, Pakistan**. It connects tourists with local hotels, car rentals, and tour guides. The architecture is **strictly decoupled** — the backend is a standalone API that serves both a Next.js web client and a future React Native mobile app.

## Tech Stack

| Layer      | Technology                                | Version   |
|------------|-------------------------------------------|-----------|
| Backend    | FastAPI + Uvicorn                         | 0.115.6   |
| ORM        | SQLModel (SQLAlchemy + Pydantic)          | 0.0.22    |
| Database   | PostgreSQL                                | 15        |
| Migrations | Alembic                                   | 1.14.1    |
| Auth       | JWT (python-jose) + bcrypt (passlib)      | 3.3.0     |
| Frontend   | Next.js (App Router) + TypeScript         | 16.x      |
| Styling    | Tailwind CSS                              | 4.x       |
| Container  | Docker + Docker Compose                   | Latest    |

## Directory Structure

```
02_GBG/
├── .env                           # All secrets (gitignored)
├── docker-compose.yml             # Orchestrates db + backend + web
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini                # Alembic config (URL overridden by env.py)
│   ├── alembic/
│   │   ├── env.py                 # Wired to SQLModel metadata + settings
│   │   ├── script.py.mako         # Migration template
│   │   └── versions/              # Auto-generated migration files
│   └── app/
│       ├── __init__.py
│       ├── main.py                # FastAPI app, CORS, lifespan, routers
│       ├── config.py              # pydantic-settings from .env
│       ├── database.py            # Async engine + session factory
│       ├── models.py              # SQLModel table definitions
│       ├── core/
│       │   ├── __init__.py
│       │   └── security.py        # Password hashing, JWT, get_current_user
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── user.py            # UserCreate, UserResponse, Token
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       └── auth.py        # /api/auth/register, login, me
│       └── routers/
│           ├── __init__.py
│           └── health.py          # GET /api/health
└── web/
    ├── Dockerfile
    ├── package.json
    └── src/app/
        ├── layout.tsx
        ├── page.tsx               # Health-check connectivity proof
        └── globals.css
```

## Database Schema

### Enums
- **UserRole**: `customer`, `admin`, `hotel_owner`, `car_rental`, `guide`
- **VerificationStatus**: `pending`, `verified`, `rejected`

### Tables
- **users** — Central user table. `role` determines which child relationships are active.
- **hotels** — Listed by `hotel_owner` users. Stores images as `text[]` (Postgres array).
- **rooms** — Belongs to a hotel. Defines room type, price, capacity, availability.
- **cars** — Listed by `car_rental` users. Requires admin verification (`status`).
- **guide_profiles** — One-to-one with a `guide` user. Stores bio, languages, daily rate, CNIC.

### Relationships
```
User ──┬── Hotel ── Room
       ├── Car
       └── GuideProfile (1:1)
```

## Authentication Architecture

### Flow
1. **Register** → `POST /api/auth/register` — Creates user, hashes password with bcrypt.
2. **Login** → `POST /api/auth/login` — Verifies credentials, returns JWT access token.
3. **Protected routes** → Include `Authorization: Bearer <token>` header.
4. **`get_current_user` dependency** → Decodes JWT, fetches user from DB, raises 401 on failure.

### Key Files
- `app/core/security.py` — `hash_password()`, `verify_password()`, `create_access_token()`, `get_current_user()`
- `app/schemas/user.py` — `UserCreate`, `UserResponse` (excludes password_hash), `Token`
- `app/api/routes/auth.py` — Register, Login, Me endpoints

### JWT Structure
- **Algorithm**: HS256
- **Payload**: `{"sub": "<user_id>", "exp": <unix_timestamp>}`
- **Expiry**: Configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` env var (default 30 min)
- **Token URL**: `/api/auth/login` (used by Swagger UI Authorize button)

### How to protect an endpoint
```python
from typing import Annotated
from fastapi import Depends
from app.core.security import get_current_user
from app.models import User

@router.get("/protected")
async def protected_route(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return {"message": f"Hello {current_user.full_name}"}
```

## Configuration
- All secrets are in the root `.env` file (gitignored).
- `app/config.py` uses `pydantic-settings` to load and validate them.
- Two database URL properties:
  - `settings.database_url` — async (asyncpg), used by the app at runtime
  - `settings.sync_database_url` — sync (psycopg2), used by Alembic

## Key Conventions
1. **API prefix**: All endpoints live under `/api/` (e.g., `/api/health`, `/api/auth/login`).
2. **Routers**: Domain routes in `app/api/routes/`, infrastructure routes in `app/routers/`.
3. **Models**: All SQLModel table classes live in `app/models.py`.
4. **Schemas**: All Pydantic input/output schemas live in `app/schemas/`.
5. **Async everywhere**: The app uses `asyncpg` and `AsyncSession` — never use sync session in request handlers.
6. **CORS**: Configured for `http://localhost:3000` + `*` for development.
7. **Passwords**: Always use `hash_password()` from `core/security.py` — never store plaintext.

## How To

### Start all services
```bash
docker-compose up --build
```

### Run Alembic migrations (inside backend container)
```bash
# Generate a new migration after model changes
docker-compose exec backend alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

### Access the services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Run locally without Docker (backend)
```bash
cd backend
pip install -r requirements.txt
# Set POSTGRES_HOST=localhost in .env first
uvicorn app.main:app --reload --port 8000
```

## Environment Variables (in .env)
| Variable                         | Purpose                             |
|----------------------------------|-------------------------------------|
| POSTGRES_USER                    | Database username                   |
| POSTGRES_PASSWORD                | Database password                   |
| POSTGRES_DB                      | Database name                       |
| POSTGRES_HOST                    | `db` in Docker, `localhost` local   |
| POSTGRES_PORT                    | PostgreSQL port (5432)              |
| CORS_ORIGINS                     | Allowed CORS origins                |
| NEXT_PUBLIC_API_URL              | Backend URL for the frontend        |
| JWT_SECRET_KEY                   | Secret for signing JWT tokens       |
| JWT_ALGORITHM                    | JWT signing algorithm (HS256)       |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES  | Token expiry in minutes (30)        |
