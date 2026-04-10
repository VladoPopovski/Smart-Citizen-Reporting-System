from __future__ import annotations

import logging
from uuid import UUID

from  datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.category import Category
from app.models.history import History
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportRead, ReportUpdate, StatusUpdate
from app.schemas.user import CurrentUser, UserRole
from app.services.ai_service import classify_text
from app.utils.duplicate_detection import check_duplicate


logger = logging.getLogger(__name__)


def _normalize_category_key(value: str) -> str:
    return value.strip().casefold()


def _classifier_label_for_category(category_name: str) -> str:
    # Help the zero-shot model understand what "Safety" means in this app.
    # Keeping other category labels untouched preserves existing behavior.
    if category_name.strip().lower() == "safety":
        return "Safety (accidents and hazards)"
    return category_name


def create_report(db: Session, *, report_in: ReportCreate, current_user: CurrentUser) -> ReportRead:
    """Persist a new report, auto-assign category (optional), and return it."""
    settings = get_settings()

    categories = db.scalars(select(Category)).all()
    category_name_key_to_id = {_normalize_category_key(c.name): c.id for c in categories}
    candidate_labels = [_classifier_label_for_category(c.name) for c in categories]
    classifier_label_key_to_id = {
        _normalize_category_key(_classifier_label_for_category(c.name)): c.id for c in categories
    }

    category_id: int | None = None

    predicted_label = None
    if settings.ai_enabled:
        try:
            predicted_label = classify_text(
                report_in.description,
                candidate_labels,
                min_confidence=settings.ai_min_confidence,
            )
        except Exception:
            logger.exception("AI classification failed.")
            predicted_label = None

    if predicted_label:
        predicted_key = _normalize_category_key(predicted_label)


        category_id = category_name_key_to_id.get(predicted_key)
        if category_id is None:
            category_id = classifier_label_key_to_id.get(predicted_key)

        if category_id is not None:
            logger.info("Auto-assigned category_id=%d ('%s')", category_id, predicted_label)
        else:
            logger.warning("AI classification label not matched to DB category: %s", predicted_label)
    else:
        if settings.ai_enabled:
            logger.warning("Classification returned None — falling back to default category.")

    if (
        settings.ai_enabled
        and predicted_label is None
        and category_id is None
        and settings.ai_default_category_name
    ):
        fallback_id = category_name_key_to_id.get(_normalize_category_key(settings.ai_default_category_name))
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


    now = datetime.now(tz=timezone.utc)

    possible_duplicate_of = check_duplicate(
        description=report_in.description,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        created_at=now,
        db=db,
    )

    if possible_duplicate_of is not None:
        logger.warning(
            "New report may be a duplicate of report id=%d — saving with flag set.",
            possible_duplicate_of,
        )

    report = Report(
        description=report_in.description,
        latitude=report_in.latitude,
        longitude=report_in.longitude,
        user_id=current_user.id,
        category_id=category_id,
        possible_duplicate_of=possible_duplicate_of,
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


def _record_status_history(
    db: Session,
    report: Report,
    new_status_id: int | None,
    changed_by_user_id: UUID,
) -> None:
    """Insert a History row capturing the old and new status of a report."""
    db.add(History(
        report_id=report.id,
        old_status_id=report.status_id,
        status_id=new_status_id,
        changed_by_user_id=changed_by_user_id,
    ))


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

    if current_user.role == UserRole.citizen:
        update_data.pop("category_id", None)
        update_data.pop("status_id", None)

    new_status_id = update_data.get("status_id", report.status_id)
    if new_status_id != report.status_id:
        _record_status_history(db, report, new_status_id, current_user.id)

    for field, value in update_data.items():
        setattr(report, field, value)

    db.commit()
    db.refresh(report)
    return ReportRead.model_validate(report)


def update_status(
    db: Session, *, report_id: int, status_in: StatusUpdate, current_user: CurrentUser
) -> ReportRead:
    """Change a report's status. Officers and admins only. Always logs history."""
    report = _get_or_404(db, report_id)

    if status_in.status_id != report.status_id:
        _record_status_history(db, report, status_in.status_id, current_user.id)

    report.status_id = status_in.status_id
    db.commit()
    db.refresh(report)
    return ReportRead.model_validate(report)


def delete_report(db: Session, *, report_id: int, current_user: CurrentUser) -> None:
    """Delete a report. Citizens can only delete their own; admins can delete any."""
    report = _get_or_404(db, report_id)
    is_owner = report.user_id == current_user.id
    allowed = current_user.role == UserRole.admin or (current_user.role == UserRole.citizen and is_owner)
    if not allowed:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(report)
    db.commit()
