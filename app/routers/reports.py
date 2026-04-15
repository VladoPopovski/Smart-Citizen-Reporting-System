from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report import CommentCreate, CommentRead, ReportCreate, ReportRead, ReportUpdate, StatusUpdate
from app.schemas.user import CurrentUser, UserRole
from app.services import report_service
from app.utils.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportRead, status_code=201)
def create_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.citizen, UserRole.admin)),
) -> ReportRead:
    """Create a citizen report. Only citizens and admins may submit reports."""
    return report_service.create_report(db, report_in=report_in, current_user=current_user)


@router.get("", response_model=list[ReportRead])
def list_reports(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[ReportRead]:
    """
    List reports.

    - Citizens see only their own reports.
    - Officers and admins see all reports.
    """
    return report_service.list_reports(db, current_user=current_user)


@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """Get a single report by ID. Citizens can only fetch their own."""
    return report_service.get_report(db, report_id=report_id, current_user=current_user)


@router.patch("/{report_id}", response_model=ReportRead)
def update_report(
    report_id: int,
    report_in: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> ReportRead:
    """
    Update a report.

    - Citizens can update description/location of their own reports only.
    - Officers and admins can update any report, including category and status.
    """
    return report_service.update_report(db, report_id=report_id, report_in=report_in, current_user=current_user)


@router.patch("/{report_id}/status", response_model=ReportRead)
def update_report_status(
    report_id: int,
    status_in: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> ReportRead:
    """Change a report's status. Officers and admins only. Always logs history."""
    return report_service.update_status(db, report_id=report_id, status_in=status_in, current_user=current_user)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a report. Citizens can only delete their own; admins can delete any."""
    report_service.delete_report(db, report_id=report_id, current_user=current_user)


@router.post("/{report_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(
    report_id: int,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(UserRole.officer, UserRole.admin)),
) -> CommentRead:
    """Add a comment to a report. Officers and admins only."""
    return report_service.create_comment(db, report_id=report_id, comment_in=comment_in, current_user=current_user)
