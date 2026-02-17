"""
GB Guide — Application Configuration

Loads settings from environment variables / .env file.
All secrets live in .env — never hardcoded.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── PostgreSQL ──────────────────────────────────────────────
    POSTGRES_USER: str = "gbg_user"
    POSTGRES_PASSWORD: str = "gbg_secret_password_change_me"
    POSTGRES_DB: str = "gbg_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # ── Derived ─────────────────────────────────────────────────
    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection string (for app runtime)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Sync PostgreSQL connection string (for Alembic migrations)."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── CORS ────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # ── App ─────────────────────────────────────────────────────
    APP_NAME: str = "GB Guide API"
    DEBUG: bool = True


# Singleton instance
settings = Settings()
