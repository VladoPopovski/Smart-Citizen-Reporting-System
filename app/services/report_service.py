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

    #  Fetch all category names from DB for classifier's choices
    categories = db.scalars(select(Category)).all()
    category_name_key_to_id = {_normalize_category_key(c.name): c.id for c in categories}
    candidate_labels = [_classifier_label_for_category(c.name) for c in categories]
    classifier_label_key_to_id = {
        _normalize_category_key(_classifier_label_for_category(c.name)): c.id for c in categories
    }

    category_id: int | None = None

    # Match category via AI (if enabled)
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

        # Prefer matching against DB category names, but also allow matching against
        # classifier-facing labels (e.g., "Safety (accidents and hazards)").
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

    # Fallback category (default: "Other")
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


#  Функциите update_report и delete_report треба да се изменат со цел да се усогласат со барањата за правилна контрола на пристап (RBAC)
#  и следење на промените во системот. Во постоечката имплементација на update_report, иако е овозможено ажурирање на извештајот, недостига механизам за евидентирање на промените на статусот.
#  Ова значи дека кога ќе се промени status_id, системот не чува информација за тоа кој ја направил промената и кога се случила. Со новата верзија се воведува зачувување на овие промени во посебна History табела,
#  со што се овозможува следење на историјата на статусите и се подобрува транспарентноста на системот. Ова е особено важно за audit trail и за исполнување на барањата на задачата.
#
# Дополнително, во функцијата delete_report постоеше логичка грешка поврзана со улогата officer. Иако според барањата officer треба да има дозвола да брише извештаи,
# во старата имплементација оваа улога не беше правилно обработена и секогаш добиваше забрана (403). Со новата логика, и admin и officer можат да бришат било кој извештај, додека citizen може да брише само свои извештаи.
# На овој начин се обезбедува правилна распределба на привилегиите според улогите.
#
# Овие измени се неопходни не само за да се подобри функционалноста, туку и за да се исполнат тест сценаријата, каде што се проверува дали правилно се применуваат правилата за пристап и дали се евидентираат промените на статусот.
# def update_report(
#     db: Session, *, report_id: int, report_in: ReportUpdate, current_user: CurrentUser
# ) -> ReportRead:
#     """
#     Update a report. Citizens can only update their own; officers/admins can update any.
#
#     FIX: Creates a History record whenever status_id changes.
#     """
#     report = _get_or_404(db, report_id)
#     if current_user.role == UserRole.citizen and report.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     update_data = report_in.model_dump(exclude_unset=True)
#
#     # Citizens may not change category or status
#     if current_user.role == UserRole.citizen:
#         update_data.pop("category_id", None)
#         update_data.pop("status_id", None)
#
#     # ✅ FIX: Track status change in History table
#     new_status_id = update_data.get("status_id")
#     if new_status_id is not None and new_status_id != report.status_id:
#         history_entry = History(
#             report_id=report.id,
#             status_id=new_status_id,
#             changed_by_user_id=current_user.id,
#         )
#         db.add(history_entry)
#
#     for field, value in update_data.items():
#         setattr(report, field, value)
#
#     db.commit()
#     db.refresh(report)
#     return ReportRead.model_validate(report)
#
#
# def delete_report(db: Session, *, report_id: int, current_user: CurrentUser) -> None:
#     """
#     Delete a report.
#
#     FIX: Officers can now delete any report (same as admins).
#     Original bug: officer role fell through the condition and always got 403.
#     """
#     report = _get_or_404(db, report_id)
#     is_owner = report.user_id == current_user.id
#
#     # Admin/officer → can delete any report
#     # Citizen → only their own
#     if current_user.role in (UserRole.admin, UserRole.officer):
#         pass  # allowed
#     elif current_user.role == UserRole.citizen and is_owner:
#         pass  # allowed
#     else:
#         raise HTTPException(status_code=403, detail="Not allowed")
#
#     db.delete(report)
#     db.commit()
