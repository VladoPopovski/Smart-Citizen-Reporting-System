"""Unit tests for rating_service.

All DB calls are mocked — no real database required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

import app.db.base  # noqa: F401
from app.schemas.user import CurrentUser, UserRole
from app.services import rating_service


def _make_user(role: UserRole = UserRole.citizen, uid=None) -> CurrentUser:
    return CurrentUser(id=uid or uuid4(), email="test@example.com", role=role)


def _make_report(user_id=None, status_id=None):
    r = MagicMock()
    r.id = uuid4()
    r.user_id = user_id or uuid4()
    r.status_id = status_id
    r.description = "Road crack"
    return r


def _make_status(sid: int, name: str):
    s = MagicMock()
    s.id = sid
    s.name = name
    return s


def _db(report=None, status=None, rating=None) -> MagicMock:
    db = MagicMock()
    db.get.side_effect = lambda model, pk: {
        "report": report,
        "status": status,
    }.get(model.__name__.lower())
    if report is not None:
        db.get.return_value = report
    return db


# ── _is_status_closed ─────────────────────────────────────────────────────────

class TestIsStatusClosed:
    def test_returns_false_for_none_status_id(self):
        db = MagicMock()
        result = rating_service._is_status_closed(db, None)
        assert result is False

    def test_returns_false_when_status_not_found(self):
        db = MagicMock()
        db.get.return_value = None
        result = rating_service._is_status_closed(db, 99)
        assert result is False

    def test_returns_true_for_closed_macedonian(self):
        status = _make_status(1, "решен")
        db = MagicMock()
        db.get.return_value = status
        assert rating_service._is_status_closed(db, 1) is True

    def test_returns_true_for_closed_english(self):
        status = _make_status(1, "closed")
        db = MagicMock()
        db.get.return_value = status
        assert rating_service._is_status_closed(db, 1) is True

    def test_returns_false_for_active_status(self):
        status = _make_status(1, "активен")
        db = MagicMock()
        db.get.return_value = status
        assert rating_service._is_status_closed(db, 1) is False

    def test_case_insensitive_match(self):
        status = _make_status(1, "РЕШЕН")
        db = MagicMock()
        db.get.return_value = status
        assert rating_service._is_status_closed(db, 1) is True

    def test_strips_whitespace_from_status_name(self):
        status = _make_status(1, "  решена  ")
        db = MagicMock()
        db.get.return_value = status
        assert rating_service._is_status_closed(db, 1) is True


# ── _get_report_or_404 ────────────────────────────────────────────────────────

class TestGetReportOr404:
    def test_returns_report_when_found(self):
        report = _make_report()
        db = MagicMock()
        db.get.return_value = report

        result = rating_service._get_report_or_404(db, report.id)

        assert result is report

    def test_raises_404_when_not_found(self):
        db = MagicMock()
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            rating_service._get_report_or_404(db, uuid4())

        assert exc_info.value.status_code == 404


# ── create_rating ─────────────────────────────────────────────────────────────

class TestCreateRating:
    def _make_rating_in(self, stars: int = 5, comment: str | None = None):
        m = MagicMock()
        m.stars = stars
        m.comment = comment
        return m

    def test_raises_403_when_not_report_owner(self):
        owner_id = uuid4()
        other_id = uuid4()
        report = _make_report(user_id=owner_id, status_id=1)
        status = _make_status(1, "решен")
        user = _make_user(role=UserRole.citizen, uid=other_id)

        db = MagicMock()
        db.get.side_effect = lambda model, pk: report if model.__name__ == "Report" else status
        db.scalars.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            rating_service.create_rating(db, report_id=report.id, rating_in=self._make_rating_in(), current_user=user)

        assert exc_info.value.status_code == 403

    def test_raises_409_when_report_not_closed(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id, status_id=1)
        active_status = _make_status(1, "активен")
        user = _make_user(role=UserRole.citizen, uid=owner_id)

        db = MagicMock()
        db.get.side_effect = lambda model, pk: report if model.__name__ == "Report" else active_status

        with pytest.raises(HTTPException) as exc_info:
            rating_service.create_rating(db, report_id=report.id, rating_in=self._make_rating_in(), current_user=user)

        assert exc_info.value.status_code == 409
        assert "closed" in exc_info.value.detail.lower()

    def test_raises_409_when_already_rated(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id, status_id=1)
        closed_status = _make_status(1, "решен")
        user = _make_user(role=UserRole.citizen, uid=owner_id)
        existing_rating = MagicMock()

        db = MagicMock()
        db.get.side_effect = lambda model, pk: report if model.__name__ == "Report" else closed_status
        db.scalars.return_value.first.return_value = existing_rating

        with pytest.raises(HTTPException) as exc_info:
            rating_service.create_rating(db, report_id=report.id, rating_in=self._make_rating_in(), current_user=user)

        assert exc_info.value.status_code == 409
        assert "already been rated" in exc_info.value.detail

    def test_raises_404_when_report_not_found(self):
        user = _make_user(role=UserRole.citizen)
        db = MagicMock()
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            rating_service.create_rating(db, report_id=uuid4(), rating_in=self._make_rating_in(), current_user=user)

        assert exc_info.value.status_code == 404


# ── get_rating ────────────────────────────────────────────────────────────────

class TestGetRating:
    def test_raises_404_when_report_not_found(self):
        user = _make_user(role=UserRole.citizen)
        db = MagicMock()
        db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            rating_service.get_rating(db, report_id=uuid4(), current_user=user)

        assert exc_info.value.status_code == 404

    def test_raises_403_when_citizen_reads_other_report(self):
        owner_id = uuid4()
        other_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(role=UserRole.citizen, uid=other_id)

        db = MagicMock()
        db.get.return_value = report
        db.scalars.return_value.first.return_value = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            rating_service.get_rating(db, report_id=report.id, current_user=user)

        assert exc_info.value.status_code == 403

    def test_officer_can_read_any_rating(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(role=UserRole.officer)
        mock_rating = MagicMock()

        db = MagicMock()
        db.get.return_value = report
        db.scalars.return_value.first.return_value = mock_rating

        with patch("app.services.rating_service.RatingRead") as MockSchema:
            MockSchema.model_validate.return_value = MagicMock()
            result = rating_service.get_rating(db, report_id=report.id, current_user=user)

        MockSchema.model_validate.assert_called_once_with(mock_rating)

    def test_raises_404_when_rating_not_found(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(role=UserRole.citizen, uid=owner_id)

        db = MagicMock()
        db.get.return_value = report
        db.scalars.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            rating_service.get_rating(db, report_id=report.id, current_user=user)

        assert exc_info.value.status_code == 404
        assert "Rating not found" in exc_info.value.detail

    def test_citizen_can_read_own_rating(self):
        owner_id = uuid4()
        report = _make_report(user_id=owner_id)
        user = _make_user(role=UserRole.citizen, uid=owner_id)
        mock_rating = MagicMock()

        db = MagicMock()
        db.get.return_value = report
        db.scalars.return_value.first.return_value = mock_rating

        with patch("app.services.rating_service.RatingRead") as MockSchema:
            MockSchema.model_validate.return_value = MagicMock()
            result = rating_service.get_rating(db, report_id=report.id, current_user=user)

        MockSchema.model_validate.assert_called_once()
