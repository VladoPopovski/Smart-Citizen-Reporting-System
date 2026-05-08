from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.report import Report
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.services.email_service import send_email_background

logger = logging.getLogger(__name__)


def create_comment_notification(
    db: Session,
    *,
    report: Report,
    commenter_user_id: UUID,
) -> None:
    if report.user_id == commenter_user_id:
        return

    title_suffix = f': "{report.description[:50]}"' if report.description else "."
    message = f"Нов коментар е додаден на вашата пријава #{report.id}{title_suffix}"

    db.add(Notification(
        user_id=report.user_id,
        report_id=report.id,
        message=message,
        is_read=False,
    ))
    logger.info(
        "Notification queued for user_id=%s on report_id=%d",
        report.user_id,
        report.id,
    )

    user = db.get(User, report.user_id)
    if user and user.email_notifications:
        send_email_background(
            user.email,
            f"Нов коментар на вашата пријава #{report.id}",
            message,
        )


def create_status_change_notification(
    db: Session,
    *,
    report: Report,
    new_status_name: str,
) -> None:
    title_suffix = f': "{report.description[:50]}"' if report.description else ""
    message = (
        f"Статусот на вашата пријава #{report.id}{title_suffix} "
        f'е променет во "{new_status_name}".'
    )
    db.add(Notification(
        user_id=report.user_id,
        report_id=report.id,
        message=message,
        is_read=False,
    ))
    logger.info(
        "Status-change notification queued for user_id=%s on report_id=%d (status=%s)",
        report.user_id,
        report.id,
        new_status_name,
    )

    user = db.get(User, report.user_id)
    if user and user.email_notifications:
        send_email_background(
            user.email,
            f"Ажурирање на пријава #{report.id}",
            message,
        )


def create_rating_invitation_notification(db: Session, *, report: Report) -> None:
    """Invite the report's owner to leave a rating after their report is closed (CR-06)."""
    title_suffix = f': "{report.description[:50]}"' if report.description else ""
    message = (
        f"Вашата пријава #{report.id}{title_suffix} е затворена. "
        "Ве молиме оставете оцена."
    )
    db.add(Notification(
        user_id=report.user_id,
        report_id=report.id,
        message=message,
        is_read=False,
    ))
    logger.info(
        "Rating-invitation notification queued for user_id=%s on report_id=%d",
        report.user_id,
        report.id,
    )

    user = db.get(User, report.user_id)
    if user and user.email_notifications:
        send_email_background(
            user.email,
            f"Оцени ја пријава #{report.id}",
            message,
        )


def list_notifications(
    db: Session,
    *,
    user_id: UUID,
    unread_only: bool = False,
) -> list[NotificationRead]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    stmt = stmt.order_by(Notification.created_at.desc())
    rows = db.scalars(stmt).all()
    return [NotificationRead.model_validate(n) for n in rows]


def mark_notification_read(
    db: Session,
    *,
    notification_id: int,
    user_id: UUID,
) -> NotificationRead | None:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user_id:
        return None
    n.is_read = True
    db.commit()
    db.refresh(n)
    return NotificationRead.model_validate(n)


def mark_all_read(db: Session, *, user_id: UUID) -> int:
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)  # noqa: E712
    ).all()
    for n in rows:
        n.is_read = True
    db.commit()
    return len(rows)


def unread_count(db: Session, *, user_id: UUID) -> int:
    return db.scalar(
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)  # noqa: E712
    ) or 0