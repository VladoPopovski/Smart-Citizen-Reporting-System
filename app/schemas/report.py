from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None


class ReportCreate(ReportBase):
    title: str | None = None


class ReportUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None
    category_id: int | None = None
    status_id: int | None = None


class StatusUpdate(BaseModel):
    status_id: int


class ReportRead(ReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    priority: str | None = None
    category_id: int | None = None
    status_id: int | None = None
    department_id: int | None = None
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    possible_duplicate_of: int | None = None