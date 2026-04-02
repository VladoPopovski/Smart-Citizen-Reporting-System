from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.report import Report
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from app.schemas.user import CurrentUser, UserRole
from app.services.ai_service import classify_text

import logging

from app.models.category import Category  # needed for DB lookup

logger = logging.getLogger(__name__)


def create_report(db: Session, *, report_in: ReportCreate, current_user: CurrentUser) -> ReportRead:
    """Persist a new report, auto-assign category via AI, and return it."""

    #  Fetch all category names from DB for classifier's choices
    categories = db.scalars(select(Category)).all()
    candidate_labels = [c.name for c in categories]

    #  Match category
    predicted_label = classify_text(report_in.description, candidate_labels)

    #  resolve the predicted name -> category_id (or None if no match / AI failed)
    category_id: int | None = None
    if predicted_label:
        matched = db.scalars(
            select(Category).where(Category.name == predicted_label)
        ).first()
        if matched:
            category_id = matched.id
            logger.info("Auto-assigned category_id=%d ('%s')", category_id, predicted_label)
        else:
            # guard
            logger.warning("No DB match for predicted label '%s' — category_id left NULL.", predicted_label)
    else:
        logger.warning("Classification returned None — category_id left NULL.")

    #  Save report with resolved category_id (may be NULL)
    report = Report(
        description=report_in.description,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        user_id=current_user.id,
        category_id=category_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportRead.model_validate(report)


def list_reports(db: Session, *, current_user: CurrentUser) -> list[ReportRead]:
    """Return reports filtered by role: citizens see only their own."""
    stmt = select(Report)
    if current_user.role == UserRole.citizen:
        stmt = stmt.where(Report.user_id == current_user.id)

    reports = db.scalars(stmt).all()
    return [ReportRead.model_validate(r) for r in reports]


def _get_or_404(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def get_report(db: Session, *, report_id: int, current_user: CurrentUser) -> ReportRead:
    """Return a single report. Citizens can only fetch their own."""
    report = _get_or_404(db, report_id)
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return ReportRead.model_validate(report)


def update_report(
    db: Session, *, report_id: int, report_in: ReportUpdate, current_user: CurrentUser
) -> ReportRead:
    """Update a report. Citizens can only update their own; officers/admins can update any."""
    report = _get_or_404(db, report_id)
    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    update_data = report_in.model_dump(exclude_unset=True)

    # Citizens may not change category or status — those are officer/admin fields
    if current_user.role == UserRole.citizen:
        update_data.pop("category_id", None)
        update_data.pop("status_id", None)

    for field, value in update_data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return ReportRead.model_validate(report)


def delete_report(db: Session, *, report_id: int, current_user: CurrentUser) -> None:
    """Delete a report. Citizens can only delete their own; admins can delete any."""
    report = _get_or_404(db, report_id)
    is_owner = report.user_id == current_user.id
    if current_user.role != UserRole.admin and not (current_user.role == UserRole.citizen and is_owner):
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(report)
    db.commit()
