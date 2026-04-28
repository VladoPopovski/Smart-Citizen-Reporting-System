from __future__ import annotations

import logging
from typing import Iterable

from fastapi import HTTPException, status as http_status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.rating import Rating
from app.models.report import Report
from app.models.status import Status
from app.schemas.rating import DepartmentRatingAvg, RatingCreate, RatingRead
from app.schemas.user import CurrentUser, UserRole

logger = logging.getLogger(__name__)

CLOSED_STATUS_NAME = "Closed"


def _is_status_closed(db: Session, status_id: int | None) -> bool:
    if status_id is None:
        return False
    row = db.get(Status, status_id)
    return row is not None and row.name == CLOSED_STATUS_NAME


def _get_report_or_404(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


def create_rating(
    db: Session,
    *,
    report_id: int,
    rating_in: RatingCreate,
    current_user: CurrentUser,
) -> RatingRead:
    """Citizen leaves a 1–5 rating on their own closed report.

    Enforces:
      - only the report's owner may rate it (citizens only — gated by router role check)
      - the report must currently be in the 'Closed' status
      - one rating per report (DB-unique on report_id catches concurrent inserts)
    """
    report = _get_report_or_404(db, report_id)

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You can only rate your own report",
        )

    if not _is_status_closed(db, report.status_id):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Only closed reports can be rated",
        )

    # Cheap pre-check; the unique constraint is the real guarantee.
    existing = db.scalars(select(Rating).where(Rating.report_id == report_id)).first()
    if existing is not None:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="This report has already been rated",
        )

    rating = Rating(
        report_id=report.id,
        citizen_id=current_user.id,
        stars=rating_in.stars,
        comment=rating_in.comment,
    )
    db.add(rating)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="This report has already been rated",
        )
    db.refresh(rating)
    return RatingRead.model_validate(rating)


def get_rating(
    db: Session,
    *,
    report_id: int,
    current_user: CurrentUser,
) -> RatingRead:
    """Fetch a report's rating. Citizens can only read ratings on their own reports."""
    report = _get_report_or_404(db, report_id)

    if current_user.role == UserRole.citizen and report.user_id != current_user.id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not allowed")

    rating = db.scalars(select(Rating).where(Rating.report_id == report_id)).first()
    if rating is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return RatingRead.model_validate(rating)


def average_ratings_by_department(db: Session) -> list[DepartmentRatingAvg]:
    """Average stars and rating count per department, for departments with ≥1 rating."""
    stmt = (
        select(
            Department.id.label("department_id"),
            Department.name.label("department_name"),
            func.avg(Rating.stars).label("avg_stars"),
            func.count(Rating.id).label("ratings_count"),
        )
        .join(Report, Report.department_id == Department.id)
        .join(Rating, Rating.report_id == Report.id)
        .group_by(Department.id, Department.name)
        .order_by(Department.name.asc())
    )
    rows: Iterable = db.execute(stmt).all()
    return [
        DepartmentRatingAvg(
            department_id=row.department_id,
            department_name=row.department_name,
            average_stars=round(float(row.avg_stars), 2),
            ratings_count=int(row.ratings_count),
        )
        for row in rows
    ]
