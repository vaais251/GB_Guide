"""
GB Guide — Alembic Environment Configuration

This file wires Alembic to our SQLModel metadata and
injects the real database URL from our Settings class.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make the backend package importable ────────────────────────
# When running `alembic` from the /backend directory, Python's
# cwd is /backend. We add it to sys.path so `from app.xxx` works.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
import app.models  # noqa: E402, F401  — force model registration
from sqlmodel import SQLModel  # noqa: E402

# ── Alembic Config ─────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with the real value from our .env
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target Metadata ────────────────────────────────────────────
# This is the metadata that Alembic's `--autogenerate` inspects.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode — generates SQL without
    connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode — connects to the database
    and applies migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
