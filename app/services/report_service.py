from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.schemas.report import ReportCreate, ReportRead
from app.schemas.user import CurrentUser
from app.services.ai_service import classify_text


def create_report(db: Session, *, report_in: ReportCreate, current_user: CurrentUser) -> ReportRead:
    """
    Placeholder report creation.

    In production you would:
    - classify text (AI)
    - persist report + related entities in PostgreSQL
    - return the created ORM object mapped to a schema
    """

    _ = db

    # Example of where AI classification would be used:
    _category_name = classify_text(report_in.description)

    # Category/status IDs would normally come from the DB.
    return ReportRead(
        id=1,
        description=report_in.description,
        category_id=None,
        status_id=None,
        user_id=current_user.id,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        created_at=datetime.now(timezone.utc),
    )


def list_reports(db: Session, *, current_user: CurrentUser) -> list[ReportRead]:
    """Placeholder list reports (structure-only)."""

    _ = (db, current_user)
    return []


def get_report(db: Session, *, report_id: int, current_user: CurrentUser) -> ReportRead:
    """Placeholder get report by ID (structure-only)."""

    _ = (db, current_user)
    return ReportRead(
        id=report_id,
        description="(mock) Report description goes here.",
        category_id=None,
        status_id=None,
        user_id=current_user.id,
        latitude=None,
        longitude=None,
        created_at=datetime.now(timezone.utc),
    )

