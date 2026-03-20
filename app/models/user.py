from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.report import Report


class UserRole(str, enum.Enum):
    citizen = "citizen"
    officer = "officer"
    admin = "admin"


class User(Base):
    """
    Application user record.

    Authentication credentials are NOT stored here (Supabase handles auth).
    You typically create/update this row after verifying a Supabase JWT.
    """

    __tablename__ = "users"

    # In a real Supabase-backed system, this would typically match the Supabase `sub` (UUID).
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        default=UserRole.citizen,
        nullable=False,
    )

    reports: Mapped[list[Report]] = relationship(back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[list[Comment]] = relationship(back_populates="user", cascade="all, delete-orphan")

