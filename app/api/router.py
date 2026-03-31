from fastapi import APIRouter

from app.routers import admin, reports, users, categories, statuses
api_router = APIRouter()

# Public / user-facing routers
api_router.include_router(users.router)
api_router.include_router(reports.router)
api_router.include_router(categories.router)
api_router.include_router(statuses.router)

# Admin-only routers
api_router.include_router(admin.router)

