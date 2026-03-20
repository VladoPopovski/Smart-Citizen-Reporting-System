from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    # Keep OpenAPI under the versioned API prefix.
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

# Versioned API routes
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Lightweight health check (no DB calls)."""
    return {"status": "ok"}

