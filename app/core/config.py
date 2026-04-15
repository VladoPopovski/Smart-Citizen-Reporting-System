from functools import lru_cache
from uuid import UUID

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

    # --- AI / ML ---
    # Auto-assign category_id on report creation (when enabled).
    ai_enabled: bool = True
    ai_preload_on_startup: bool = False
    # 0 disables the threshold (always accept the top label).
    ai_min_confidence: float = 0.0
    ai_default_category_name: str = "Other"
    ai_cache_ttl_seconds: int = 300

    # HuggingFace zero-shot classification defaults
    ai_hf_model: str = "facebook/bart-large-mnli"
    ai_hf_revision: str | None = None
    ai_hf_device: int = -1

    # OpenAI fallback (only used when HuggingFace fails / returns None)
    ai_openai_fallback_enabled: bool = False
    ai_openai_model: str = "gpt-4o-mini"
    ai_openai_timeout_seconds: float = 15.0
    openai_api_key: str | None = None

    # Optional: persist an AI-generated confirmation message as a Comment.
    # Must reference an existing user UUID in the `users` table.
    ai_confirmation_comment_user_id: UUID | None = None


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (import-safe)."""
    return Settings()

