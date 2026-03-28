from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration.

    Values are loaded from environment variables and optionally a `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    project_name: str = "Smart Citizen Complaint Management System"
    api_v1_str: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smart_citizen"

    # Supabase integration (placeholders):
    # - In production you would validate JWT signatures using Supabase JWKS.
    # - This template intentionally *does not* integrate Supabase SDKs.
    supabase_mock_verify: bool = True
    dev_skip_auth: bool = False


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (import-safe)."""
    return Settings()

