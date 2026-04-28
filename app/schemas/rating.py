from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RatingCreate(BaseModel):
    stars: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str | None = Field(default=None, max_length=2000)


class RatingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    citizen_id: UUID
    stars: int
    comment: str | None = None
    created_at: datetime


class DepartmentRatingAvg(BaseModel):
    """Aggregate rating stats for a single department."""

    department_id: int | None = None
    department_name: str | None = None
    average_stars: float
    ratings_count: int
