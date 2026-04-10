from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    """Base fields shared across report schemas."""

    description: str = Field(..., min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None


class ReportCreate(ReportBase):
    """
    Schema used when creating a new report.
    Category and status are assigned later by the system.
    """
    pass


class ReportUpdate(BaseModel):
    """Schema used for updating an existing report."""

    description: str | None = Field(default=None, min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None
    category_id: int | None = None
    status_id: int | None = None


class StatusUpdate(BaseModel):
    status_id: int


class ReportRead(ReportBase):
    """Schema returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int | None = None
    status_id: int | None = None
    user_id: UUID
    created_at: datetime
    possible_duplicate_of: int | None = None
