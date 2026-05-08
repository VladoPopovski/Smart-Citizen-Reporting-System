"""Unit tests for user_service.

All DB calls are mocked — no real database required.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

import app.db.base  # noqa: F401 — ensures models are registered
from app.models.user import UserRole
from app.services import user_service


def _db() -> MagicMock:
    db = MagicMock()
    db.get.return_value = None
    return db


def _make_user(uid=None, email="user@example.com", role=UserRole.citizen, email_notifications=True):
    u = MagicMock()
    u.id = uid or uuid4()
    u.email = email
    u.role = role
    u.email_notifications = email_notifications
    return u


# ── upsert_user ───────────────────────────────────────────────────────────────

class TestUpsertUser:
    def test_creates_new_user_when_not_found(self):
        uid = uuid4()
        db = _db()
        db.get.return_value = None

        result = user_service.upsert_user(db, user_id=uid, email="new@example.com", role=UserRole.citizen)

        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_new_user_gets_provided_role(self):
        uid = uuid4()
        db = _db()

        # We can't inspect the User() constructor directly with MagicMock db,
        # so we check add was called with an object having correct attributes
        added_objects = []
        db.add.side_effect = lambda obj: added_objects.append(obj)
        db.get.return_value = None

        user_service.upsert_user(db, user_id=uid, email="a@b.com", role=UserRole.officer)

        assert len(added_objects) == 1
        new_user = added_objects[0]
        assert new_user.role == UserRole.officer

    def test_new_user_defaults_to_citizen_when_no_role(self):
        uid = uuid4()
        db = _db()
        added_objects = []
        db.add.side_effect = lambda obj: added_objects.append(obj)
        db.get.return_value = None

        user_service.upsert_user(db, user_id=uid, email="a@b.com", role=None)

        new_user = added_objects[0]
        assert new_user.role == UserRole.citizen

    def test_generates_placeholder_email_when_none(self):
        uid = uuid4()
        db = _db()
        added_objects = []
        db.add.side_effect = lambda obj: added_objects.append(obj)

        user_service.upsert_user(db, user_id=uid, email=None)

        new_user = added_objects[0]
        assert "@unknown.local" in new_user.email
        assert str(uid) in new_user.email

    def test_existing_user_email_updated(self):
        uid = uuid4()
        existing = _make_user(uid=uid, email="old@example.com")
        db = _db()
        db.get.return_value = existing

        user_service.upsert_user(db, user_id=uid, email="new@example.com")

        assert existing.email == "new@example.com"
        db.commit.assert_called_once()

    def test_existing_user_no_commit_when_email_unchanged(self):
        uid = uuid4()
        existing = _make_user(uid=uid, email="same@example.com")
        db = _db()
        db.get.return_value = existing

        result = user_service.upsert_user(db, user_id=uid, email="same@example.com")

        db.commit.assert_not_called()

    def test_existing_user_keeps_email_when_none_provided(self):
        uid = uuid4()
        existing = _make_user(uid=uid, email="keep@example.com")
        db = _db()
        db.get.return_value = existing

        user_service.upsert_user(db, user_id=uid, email=None)

        assert existing.email == "keep@example.com"

    def test_returns_user(self):
        uid = uuid4()
        existing = _make_user(uid=uid)
        db = _db()
        db.get.return_value = existing

        result = user_service.upsert_user(db, user_id=uid, email=existing.email)

        assert result is existing


# ── update_user_role ──────────────────────────────────────────────────────────

class TestUpdateUserRole:
    def test_raises_when_user_not_found(self):
        db = _db()
        db.get.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_role(db, user_id=uuid4(), role=UserRole.admin)

    def test_updates_role(self):
        uid = uuid4()
        user = _make_user(uid=uid, role=UserRole.citizen)
        db = _db()
        db.get.return_value = user

        user_service.update_user_role(db, user_id=uid, role=UserRole.officer)

        assert user.role == UserRole.officer
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(user)

    def test_returns_updated_user(self):
        uid = uuid4()
        user = _make_user(uid=uid)
        db = _db()
        db.get.return_value = user

        result = user_service.update_user_role(db, user_id=uid, role=UserRole.admin)

        assert result is user

    def test_can_demote_admin_to_citizen(self):
        uid = uuid4()
        user = _make_user(uid=uid, role=UserRole.admin)
        db = _db()
        db.get.return_value = user

        user_service.update_user_role(db, user_id=uid, role=UserRole.citizen)

        assert user.role == UserRole.citizen


# ── update_user_settings ──────────────────────────────────────────────────────

class TestUpdateUserSettings:
    def test_raises_when_user_not_found(self):
        db = _db()
        db.get.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            user_service.update_user_settings(db, user_id=uuid4(), email_notifications=True)

    def test_disables_email_notifications(self):
        uid = uuid4()
        user = _make_user(uid=uid, email_notifications=True)
        db = _db()
        db.get.return_value = user

        user_service.update_user_settings(db, user_id=uid, email_notifications=False)

        assert user.email_notifications is False
        db.commit.assert_called_once()

    def test_enables_email_notifications(self):
        uid = uuid4()
        user = _make_user(uid=uid, email_notifications=False)
        db = _db()
        db.get.return_value = user

        user_service.update_user_settings(db, user_id=uid, email_notifications=True)

        assert user.email_notifications is True

    def test_returns_updated_user(self):
        uid = uuid4()
        user = _make_user(uid=uid)
        db = _db()
        db.get.return_value = user

        result = user_service.update_user_settings(db, user_id=uid, email_notifications=False)

        assert result is user
        db.refresh.assert_called_once_with(user)
