from fastapi import APIRouter

from app.routers import admin, reports, users

api_router = APIRouter()

# Public / user-facing routers
api_router.include_router(users.router)
api_router.include_router(reports.router)

# Admin-only routers
api_router.include_router(admin.router)

