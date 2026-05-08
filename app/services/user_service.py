from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User, UserRole


def upsert_user(
    db: Session,
    *,
    user_id: UUID,
    email: str | None,
    role: UserRole | None = None,
) -> User:
    """Create or update a user.

    ``role`` is only applied when explicitly provided (not None).
    For existing users this preserves the DB-managed role when the
    caller has no authoritative role information (e.g. JWT has no claim).
    """
    user = db.get(User, user_id)

    if user is None:
        user = User(
            id=user_id,
            email=email or f"{user_id}@unknown.local",
            role=role if role is not None else UserRole.citizen,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    changed = False
    next_email = email or user.email
    if user.email != next_email:
        user.email = next_email
        changed = True

    if changed:
        db.commit()
        db.refresh(user)

    return user


def update_user_role(
    db: Session,
    *,
    user_id: UUID,
    role: UserRole,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def update_user_settings(
    db: Session,
    *,
    user_id: UUID,
    email_notifications: bool,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("User not found")
    user.email_notifications = email_notifications
    db.commit()
    db.refresh(user)
    return user
