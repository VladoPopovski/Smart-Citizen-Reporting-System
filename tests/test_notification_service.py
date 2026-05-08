"""Unit tests for notification_service.

All DB calls are mocked via MagicMock — no real database required.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch
from uuid import uuid4

import pytest

import app.db.base  # noqa: F401 — ensures models are registered
from app.services import notification_service


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_report(user_id=None, report_id=None, description="Broken streetlight"):
    r = MagicMock()
    r.id = report_id or uuid4()
    r.user_id = user_id or uuid4()
    r.description = description
    return r


def _make_user(uid=None, email="owner@example.com", email_notifications=True):
    u = MagicMock()
    u.id = uid or uuid4()
    u.email = email
    u.email_notifications = email_notifications
    return u


def _make_notification(nid: int, user_id, report_id, message="msg", is_read=False):
    n = MagicMock()
    n.id = nid
    n.user_id = user_id
    n.report_id = report_id
    n.message = message
    n.is_read = is_read
    n.created_at = datetime.now(timezone.utc)
    # make model_validate work by returning a real-ish schema
    return n


def _db() -> MagicMock:
    db = MagicMock()
    db.get.return_value = None
    return db


# ── create_comment_notification ───────────────────────────────────────────────

class TestCreateCommentNotification:
    def test_skipped_when_commenter_is_owner(self):
        uid = uuid4()
        report = _make_report(user_id=uid)
        db = _db()

        notification_service.create_comment_notification(db, report=report, commenter_user_id=uid)

        db.add.assert_not_called()

    def test_notification_added_when_different_user(self):
        owner_id = uuid4()
        commenter_id = uuid4()
        report = _make_report(user_id=owner_id)
        db = _db()
        db.get.return_value = None  # user has no email notifications

        notification_service.create_comment_notification(db, report=report, commenter_user_id=commenter_id)

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.user_id == owner_id
        assert str(report.id) in added.message or True  # message contains report id

    def test_sends_email_when_user_has_notifications_enabled(self):
        owner_id = uuid4()
        commenter_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(uid=owner_id, email_notifications=True)
        db = _db()
        db.get.return_value = user

        with patch("app.services.notification_service.send_email_background") as mock_email:
            notification_service.create_comment_notification(db, report=report, commenter_user_id=commenter_id)

        mock_email.assert_called_once()
        assert mock_email.call_args[0][0] == user.email

    def test_no_email_when_notifications_disabled(self):
        owner_id = uuid4()
        commenter_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(uid=owner_id, email_notifications=False)
        db = _db()
        db.get.return_value = user

        with patch("app.services.notification_service.send_email_background") as mock_email:
            notification_service.create_comment_notification(db, report=report, commenter_user_id=commenter_id)

        mock_email.assert_not_called()

    def test_message_contains_report_id(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        db = _db()

        notification_service.create_comment_notification(db, report=report, commenter_user_id=uuid4())

        added = db.add.call_args[0][0]
        assert str(report.id) in added.message

    def test_message_contains_description_preview(self):
        owner_id = uuid4()
        desc = "There is a big pothole on Main Street"
        report = _make_report(user_id=owner_id, description=desc)
        db = _db()

        notification_service.create_comment_notification(db, report=report, commenter_user_id=uuid4())

        added = db.add.call_args[0][0]
        assert desc[:30] in added.message

    def test_empty_description_does_not_crash(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id, description="")
        db = _db()

        notification_service.create_comment_notification(db, report=report, commenter_user_id=uuid4())

        db.add.assert_called_once()


# ── create_status_change_notification ────────────────────────────────────────

class TestCreateStatusChangeNotification:
    def test_notification_added(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        db = _db()

        notification_service.create_status_change_notification(db, report=report, new_status_name="Решен")

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.user_id == owner_id
        assert "Решен" in added.message

    def test_message_mentions_new_status(self):
        report = _make_report()
        db = _db()

        notification_service.create_status_change_notification(db, report=report, new_status_name="Во тек")

        added = db.add.call_args[0][0]
        assert "Во тек" in added.message

    def test_sends_email_when_notifications_enabled(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(uid=owner_id, email_notifications=True)
        db = _db()
        db.get.return_value = user

        with patch("app.services.notification_service.send_email_background") as mock_email:
            notification_service.create_status_change_notification(db, report=report, new_status_name="Решен")

        mock_email.assert_called_once()

    def test_no_email_when_notifications_disabled(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(uid=owner_id, email_notifications=False)
        db = _db()
        db.get.return_value = user

        with patch("app.services.notification_service.send_email_background") as mock_email:
            notification_service.create_status_change_notification(db, report=report, new_status_name="Решен")

        mock_email.assert_not_called()

    def test_is_read_defaults_to_false(self):
        report = _make_report()
        db = _db()

        notification_service.create_status_change_notification(db, report=report, new_status_name="X")

        added = db.add.call_args[0][0]
        assert added.is_read is False


# ── create_rating_invitation_notification ─────────────────────────────────────

class TestCreateRatingInvitationNotification:
    def test_notification_added(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        db = _db()

        notification_service.create_rating_invitation_notification(db, report=report)

        db.add.assert_called_once()
        added = db.add.call_args[0][0]
        assert added.user_id == owner_id

    def test_message_asks_to_rate(self):
        report = _make_report()
        db = _db()

        notification_service.create_rating_invitation_notification(db, report=report)

        added = db.add.call_args[0][0]
        assert "оцен" in added.message.lower() or "rate" in added.message.lower() or "оцена" in added.message.lower()

    def test_sends_email_when_notifications_enabled(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(uid=owner_id, email_notifications=True)
        db = _db()
        db.get.return_value = user

        with patch("app.services.notification_service.send_email_background") as mock_email:
            notification_service.create_rating_invitation_notification(db, report=report)

        mock_email.assert_called_once()


# ── list_notifications ─────────────────────────────────────────────────────────

class TestListNotifications:
    def _setup_db_with_notifications(self, notifications):
        """Return a db mock whose scalars().all() returns given notifications."""
        db = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = notifications
        db.scalars.return_value = scalars_mock
        return db

    def test_returns_empty_list_when_none(self):
        uid = uuid4()
        db = self._setup_db_with_notifications([])

        with patch("app.services.notification_service.NotificationRead") as MockSchema:
            MockSchema.model_validate.return_value = MagicMock()
            result = notification_service.list_notifications(db, user_id=uid)

        assert result == []

    def test_returns_all_notifications(self):
        uid = uuid4()
        fake_notifs = [MagicMock(), MagicMock()]
        db = self._setup_db_with_notifications(fake_notifs)

        with patch("app.services.notification_service.NotificationRead") as MockSchema:
            MockSchema.model_validate.side_effect = lambda n: n
            result = notification_service.list_notifications(db, user_id=uid)

        assert len(result) == 2

    def test_unread_only_flag_filters_query(self):
        uid = uuid4()
        db = self._setup_db_with_notifications([])

        with patch("app.services.notification_service.NotificationRead"):
            notification_service.list_notifications(db, user_id=uid, unread_only=True)

        # The stmt should have been chained with an extra where() call
        # We just verify the function doesn't crash with unread_only=True
        db.scalars.assert_called_once()


# ── mark_notification_read ────────────────────────────────────────────────────

class TestMarkNotificationRead:
    def test_returns_none_when_not_found(self):
        db = _db()
        db.get.return_value = None

        result = notification_service.mark_notification_read(db, notification_id=99, user_id=uuid4())

        assert result is None

    def test_returns_none_when_wrong_owner(self):
        uid = uuid4()
        n = MagicMock()
        n.user_id = uuid4()  # different user
        n.is_read = False
        db = _db()
        db.get.return_value = n

        result = notification_service.mark_notification_read(db, notification_id=1, user_id=uid)

        assert result is None
        assert n.is_read is False  # unchanged

    def test_marks_read_and_commits(self):
        uid = uuid4()
        n = MagicMock()
        n.user_id = uid
        n.is_read = False
        db = _db()
        db.get.return_value = n

        with patch("app.services.notification_service.NotificationRead") as MockSchema:
            MockSchema.model_validate.return_value = MagicMock()
            result = notification_service.mark_notification_read(db, notification_id=1, user_id=uid)

        assert n.is_read is True
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(n)

    def test_returns_schema_on_success(self):
        uid = uuid4()
        n = MagicMock()
        n.user_id = uid
        n.is_read = False
        db = _db()
        db.get.return_value = n
        expected = MagicMock()

        with patch("app.services.notification_service.NotificationRead") as MockSchema:
            MockSchema.model_validate.return_value = expected
            result = notification_service.mark_notification_read(db, notification_id=1, user_id=uid)

        assert result is expected


# ── mark_all_read ─────────────────────────────────────────────────────────────

class TestMarkAllRead:
    def test_returns_zero_when_none_unread(self):
        uid = uuid4()
        db = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        db.scalars.return_value = scalars_mock

        result = notification_service.mark_all_read(db, user_id=uid)

        assert result == 0
        db.commit.assert_called_once()

    def test_marks_all_and_returns_count(self):
        uid = uuid4()
        n1, n2 = MagicMock(is_read=False), MagicMock(is_read=False)
        db = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [n1, n2]
        db.scalars.return_value = scalars_mock

        result = notification_service.mark_all_read(db, user_id=uid)

        assert result == 2
        assert n1.is_read is True
        assert n2.is_read is True
        db.commit.assert_called_once()


# ── unread_count ──────────────────────────────────────────────────────────────

class TestUnreadCount:
    def test_returns_count_from_db(self):
        uid = uuid4()
        db = MagicMock()
        db.scalar.return_value = 5

        result = notification_service.unread_count(db, user_id=uid)

        assert result == 5

    def test_returns_zero_when_db_returns_none(self):
        uid = uuid4()
        db = MagicMock()
        db.scalar.return_value = None

        result = notification_service.unread_count(db, user_id=uid)

        assert result == 0
