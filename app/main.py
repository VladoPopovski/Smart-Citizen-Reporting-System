from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import app.db.base  # noqa: F401
from app.api.router import api_router
from app.core.config import get_settings
from app.services.ai_service import warmup_model
from app.utils.dependencies import DEV_USER, get_current_user
from app.utils.file_upload import UPLOAD_DIR

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

if settings.dev_skip_auth:
    app.dependency_overrides[get_current_user] = lambda: DEV_USER

# Serve uploaded files at /static/uploads/<filename>
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Versioned API routes
app.include_router(api_router, prefix=settings.api_v1_str)


@app.on_event("startup")
def _startup_warmup_ai() -> None:
    if settings.ai_enabled and settings.ai_preload_on_startup:
        warmup_model()


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Lightweight health check (no DB calls)."""
    return {"status": "ok"}