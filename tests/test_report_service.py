"""Unit tests for report_service.

The DB session and Report model are replaced with MagicMocks so no real
database or SQLAlchemy instrumentation is needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.user import CurrentUser, UserRole
from app.services import report_service


def _make_user(role: UserRole, uid=None) -> CurrentUser:
    return CurrentUser(id=uid or uuid4(), email="test@example.com", role=role)


def _make_report(user_id=None, report_id: int = 1) -> MagicMock:
    r = MagicMock()
    r.id = report_id
    r.description = "Broken streetlight"
    r.category_id = None
    r.status_id = None
    r.user_id = user_id or uuid4()
    r.latitude = None
    r.longitude = None
    r.created_at = datetime.now(timezone.utc)
    return r


def _db(report=None) -> MagicMock:
    """Return a mock Session with db.get() pre-configured."""
    db = MagicMock()
    db.get.return_value = report
    return db


def _report_in(**fields) -> MagicMock:
    """Mock a ReportUpdate with model_dump returning only the given fields."""
    m = MagicMock()
    m.model_dump.return_value = fields
    return m


class TestGetReport:
    def test_citizen_gets_own_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        result = report_service.get_report(_db(report), report_id=1, current_user=user)
        assert result.id == report.id

    def test_citizen_cannot_get_other_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=uuid4())
        with pytest.raises(HTTPException) as exc:
            report_service.get_report(_db(report), report_id=1, current_user=user)
        assert exc.value.status_code == 403

    def test_officer_can_get_any_report(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        result = report_service.get_report(
            _db(report), report_id=1, current_user=officer
        )
        assert result.id == report.id

    def test_admin_can_get_any_report(self):
        admin = _make_user(UserRole.admin)
        report = _make_report(user_id=uuid4())
        result = report_service.get_report(_db(report), report_id=1, current_user=admin)
        assert result.id == report.id

    def test_missing_report_raises_404(self):
        user = _make_user(UserRole.citizen)
        with pytest.raises(HTTPException) as exc:
            report_service.get_report(_db(None), report_id=99, current_user=user)
        assert exc.value.status_code == 404


class TestUpdateReport:
    def test_citizen_updates_own_report_description(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        db = _db(report)

        report_service.update_report(
            db,
            report_id=1,
            report_in=_report_in(description="New text"),
            current_user=user,
        )

        assert report.description == "New text"
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(report)

    def test_citizen_cannot_update_other_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=uuid4())
        with pytest.raises(HTTPException) as exc:
            report_service.update_report(
                _db(report),
                report_id=1,
                report_in=_report_in(description="x"),
                current_user=user,
            )
        assert exc.value.status_code == 403

    def test_citizen_cannot_set_status_or_category(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        db = _db(report)

        report_service.update_report(
            db,
            report_id=1,
            report_in=_report_in(status_id=2, category_id=3),
            current_user=user,
        )

        # setattr must NOT have been called with these fields
        assert report.status_id is None
        assert report.category_id is None

    def test_officer_can_set_status_and_category(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=uuid4())
        db = _db(report)

        report_service.update_report(
            db,
            report_id=1,
            report_in=_report_in(status_id=2, category_id=3),
            current_user=officer,
        )

        assert report.status_id == 2
        assert report.category_id == 3

    def test_missing_report_raises_404(self):
        user = _make_user(UserRole.citizen)
        with pytest.raises(HTTPException) as exc:
            report_service.update_report(
                _db(None),
                report_id=99,
                report_in=_report_in(description="x"),
                current_user=user,
            )
        assert exc.value.status_code == 404


class TestDeleteReport:
    def test_citizen_deletes_own_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=user.id)
        db = _db(report)
        report_service.delete_report(db, report_id=1, current_user=user)
        db.delete.assert_called_once_with(report)
        db.commit.assert_called_once()

    def test_citizen_cannot_delete_other_report(self):
        user = _make_user(UserRole.citizen)
        report = _make_report(user_id=uuid4())
        with pytest.raises(HTTPException) as exc:
            report_service.delete_report(_db(report), report_id=1, current_user=user)
        assert exc.value.status_code == 403

    def test_officer_cannot_delete_any_report(self):
        officer = _make_user(UserRole.officer)
        report = _make_report(user_id=officer.id)  # even their own
        with pytest.raises(HTTPException) as exc:
            report_service.delete_report(_db(report), report_id=1, current_user=officer)
        assert exc.value.status_code == 403

    def test_admin_deletes_any_report(self):
        admin = _make_user(UserRole.admin)
        report = _make_report(user_id=uuid4())
        db = _db(report)
        report_service.delete_report(db, report_id=1, current_user=admin)
        db.delete.assert_called_once_with(report)

    def test_missing_report_raises_404(self):
        admin = _make_user(UserRole.admin)
        with pytest.raises(HTTPException) as exc:
            report_service.delete_report(_db(None), report_id=99, current_user=admin)
        assert exc.value.status_code == 404


class TestListReports:
    def test_citizen_sees_only_own_reports(self):
        user = _make_user(UserRole.citizen)
        own = _make_report(user_id=user.id, report_id=1)
        db = MagicMock()
        db.scalars.return_value.all.return_value = [own]

        results = report_service.list_reports(db, current_user=user)

        assert len(results) == 1
        assert results[0].user_id == user.id

    def test_admin_sees_all_reports(self):
        admin = _make_user(UserRole.admin)
        r1 = _make_report(user_id=uuid4(), report_id=1)
        r2 = _make_report(user_id=uuid4(), report_id=2)
        db = MagicMock()
        db.scalars.return_value.all.return_value = [r1, r2]

        results = report_service.list_reports(db, current_user=admin)
        assert len(results) == 2
