from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    """
    Input schema for creating a report.

    Category/status are intentionally omitted here; the system can assign them later
    (e.g., via AI classification + workflow rules).
    """

    description: str = Field(min_length=1, max_length=5000)
    latitude: float | None = None
    longitude: float | None = None


class ReportRead(BaseModel):
    """Output schema for report responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    category_id: int | None = None
    status_id: int | None = None
    user_id: UUID
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime

