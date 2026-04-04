from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.category import Category
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate
from app.schemas.user import CurrentUser, UserRole
from app.services.ai_service import classify_text

import logging

logger = logging.getLogger(__name__)


def _classifier_label_for_category(category_name: str) -> str:
    # Help the zero-shot model understand what "Safety" means in this app.
    # Keeping other category labels untouched preserves existing behavior.
    if category_name.strip().lower() == "safety":
        return "Safety (accidents and hazards)"
    return category_name


def create_report(db: Session, *, report_in: ReportCreate, current_user: CurrentUser) -> ReportRead:
    """Persist a new report, auto-assign category (optional), and return it."""
    settings = get_settings()

    #  Fetch all category names from DB for classifier's choices
    categories = db.scalars(select(Category)).all()
    category_name_to_id = {c.name: c.id for c in categories}
    label_to_id = {_classifier_label_for_category(name): cid for name, cid in category_name_to_id.items()}
    candidate_labels = list(label_to_id.keys())

    category_id: int | None = None

    # Match category via AI (if enabled)
    predicted_label = None
    if settings.ai_enabled:
        predicted_label = classify_text(
            report_in.description,
            candidate_labels,
            min_confidence=settings.ai_min_confidence,
        )

    if predicted_label:
        matched_id = label_to_id.get(predicted_label)
        if matched_id is not None:
            category_id = matched_id
            logger.info("Auto-assigned category_id=%d ('%s')", category_id, predicted_label)
        else:
            # Guard: predicted label should always be one of candidate_labels.
            logger.warning(
                "No DB match for predicted label '%s' — will fall back.",
                predicted_label,
            )
    else:
        if settings.ai_enabled:
            logger.warning("Classification returned None — falling back to default category.")

    # Fallback category (default: "Other")
    if settings.ai_enabled and category_id is None and settings.ai_default_category_name:
        fallback_id = category_name_to_id.get(settings.ai_default_category_name)
        if fallback_id is not None:
            category_id = fallback_id
            logger.info(
                "Applied fallback category_id=%d ('%s')",
                category_id,
                settings.ai_default_category_name,
            )
        else:
            logger.warning(
                "Fallback category '%s' not found in DB — category_id left NULL.",
                settings.ai_default_category_name,
            )

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
