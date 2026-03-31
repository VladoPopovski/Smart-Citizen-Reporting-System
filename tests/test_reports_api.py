"""
API Integration Tests — /api/v1/reports
========================================
Вкупно: 15 тестови

Барања:
  - PostgreSQL база да е стартувана и достапна
  - DEV_SKIP_AUTH=true (или поставено во .env)
  - Миграциите да се применети

Стартување:
  python -m pytest tests/test_reports_api.py -v

1. Проверува дека можеш да креираш репорт со минимален payload и добиваш 201 статус; ✅ Важи како TestClient POST integration тест со DEV_SKIP_AUTH=true
2. Проверува дека репорт со latitude и longitude се креира правилно со 201 статус; ✅ TestClient POST integration тест
3. Проверува дека празен description предизвикува validation error 422; ✅ TestClient POST validation тест
4. Проверува дека пропуштен description предизвикува validation error 422; ✅ TestClient POST validation тест
5. Проверува дека admin може да ги види сите креирани репорти со GET list 200; ✅ TestClient GET list integration тест
6. Проверува дека можеш да земеш репорт по ID и полето description е точно со GET 200; ✅ TestClient GET single integration тест
7. Проверува дека барање на непостоечки репорт враќа 404; ✅ TestClient GET single edge case
8. Проверува дека admin може да ја ажурира description на репортот со PATCH; ✅ TestClient PATCH integration тест
9. Проверува дека admin може да ги смени status_id и category_id на репортот со PATCH; ✅ TestClient PATCH integration тест
10. Проверува дека можеш да избришеш репорт и подоцна не може да се пристапи до него; ✅ TestClient DELETE интеграција
11. Проверува дека citizen не може да го види туѓ репорт и добива 403; ✅ TestClient GET forbidden тест
12. Проверува дека citizen не може да ја промени description на туѓ репорт и добива 403; ✅ TestClient PATCH forbidden тест (не смее да смени статус)
13. Проверува дека officer има пристап до сите репорти со GET list 200; ✅ TestClient GET list integration тест
14. Проверува дека description до максимална должина се прифаќа (201), а над тоа предизвикува 422; ✅ TestClient POST validation тест
15. Проверува дека patch на непостоечки репорт враќа 404; ✅ TestClient PATCH edge case
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


os.environ["DEV_SKIP_AUTH"] = "true"

from app.core.config import get_settings
get_settings.cache_clear()

from app.db.session import SessionLocal
from app.main import app
from app.models.report import Report
from app.schemas.user import CurrentUser, UserRole
from app.utils.dependencies import DEV_USER, get_current_user


PREFIX      = "/api/v1/reports"
DEV_USER_ID = str(DEV_USER.id)


CITIZEN_USER = CurrentUser(
    id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    email="citizen_test@example.com",
    role=UserRole.citizen,
)

OFFICER_USER = CurrentUser(
    id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    email="officer@example.com",
    role=UserRole.officer,
)

VALID_PAYLOAD = {
    "description": "Скршена улична светилка кај плоштадот.",
}

VALID_PAYLOAD_WITH_LOCATION = {
    "description": "Расипан водовод на улица Питу Гули.",
    "latitude": 41.9965,
    "longitude": 21.4314,
}

_CLEANUP_PREFIXES = [
    "Скршена улична светилка%",
    "Расипан водовод%",
    "Тест:%",
    "PATCH тест%",
    "Ќе биде избришан%",
    "Долг опис%",
    "Officer%",
]







@pytest.fixture()
def client() -> Generator[TestClient, None, None]:

    app.dependency_overrides[get_current_user] = lambda: DEV_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides[get_current_user] = lambda: DEV_USER


@pytest.fixture(autouse=True)
def cleanup_reports():

    yield
    db: Session = SessionLocal()
    try:
        from sqlalchemy import or_
        conditions = [Report.description.like(p) for p in _CLEANUP_PREFIXES]
        db.query(Report).filter(or_(*conditions)).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _create(client: TestClient, payload: dict | None = None) -> dict:

    resp = client.post(PREFIX, json=payload or VALID_PAYLOAD)
    assert resp.status_code == 201, f"Неуспешно креирање: {resp.text}"
    return resp.json()


# ═════════════════════════════════════════════════════════════════════════════
# ТЕСТОВИ
# ═════════════════════════════════════════════════════════════════════════════

def test_01_create_report_minimal_payload(client: TestClient):
    resp = client.post(PREFIX, json=VALID_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == VALID_PAYLOAD["description"]
    assert "id" in body
    assert "user_id" in body
    assert "created_at" in body
    assert body["category_id"] is None
    assert body["status_id"] is None


def test_02_create_report_with_location(client: TestClient):
    resp = client.post(PREFIX, json=VALID_PAYLOAD_WITH_LOCATION)
    assert resp.status_code == 201
    body = resp.json()
    assert body["latitude"] == pytest.approx(41.9965)
    assert body["longitude"] == pytest.approx(21.4314)


def test_03_create_report_empty_description_fails(client: TestClient):
    resp = client.post(PREFIX, json={"description": ""})
    assert resp.status_code == 422
    fields = [e["loc"][-1] for e in resp.json()["detail"]]
    assert "description" in fields


def test_04_create_report_missing_description_fails(client: TestClient):
    resp = client.post(PREFIX, json={"latitude": 41.99})
    assert resp.status_code == 422


def test_05_list_reports_admin_sees_all(client: TestClient):
    created = _create(client)
    report_id = created["id"]
    resp = client.get(PREFIX)
    assert resp.status_code == 200
    assert report_id in [r["id"] for r in resp.json()]


def test_06_get_report_by_id(client: TestClient):
    created = _create(client)
    report_id = created["id"]
    resp = client.get(f"{PREFIX}/{report_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == report_id
    assert body["description"] == VALID_PAYLOAD["description"]
    assert body["user_id"] == DEV_USER_ID


def test_07_get_report_not_found(client: TestClient):
    resp = client.get(f"{PREFIX}/999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_08_patch_report_description(client: TestClient):
    created = _create(client, {"description": "PATCH тест: оригинален опис."})
    report_id = created["id"]
    resp = client.patch(
        f"{PREFIX}/{report_id}",
        json={"description": "PATCH тест: ажуриран опис."},
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "PATCH тест: ажуриран опис."


def test_09_patch_admin_can_change_status_and_category(client: TestClient):
    created = _create(client, {"description": "Тест: admin status patch."})
    report_id = created["id"]
    resp = client.patch(
        f"{PREFIX}/{report_id}",
        json={"status_id": 1, "category_id": 1},
    )
    assert resp.status_code == 200
    assert resp.json()["status_id"] == 1
    assert resp.json()["category_id"] == 1


def test_10_delete_report(client: TestClient):
    created = _create(client, {"description": "Ќе биде избришан."})
    report_id = created["id"]
    assert client.delete(f"{PREFIX}/{report_id}").status_code == 204
    assert client.get(f"{PREFIX}/{report_id}").status_code == 404


def test_11_get_report_forbidden_for_citizen(client: TestClient):

    db: Session = SessionLocal()
    try:
        report = Report(description="Тест: туѓ репорт за citizen.", user_id=DEV_USER.id)
        db.add(report)
        db.commit()
        db.refresh(report)
        report_id = report.id
    finally:
        db.close()


    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    try:
        resp = client.get(f"{PREFIX}/{report_id}")
        assert resp.status_code == 403
        assert "not allowed" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_12_citizen_cannot_patch_foreign_report(client: TestClient):

    db: Session = SessionLocal()
    try:
        report = Report(description="Тест: citizen patch туѓ.", user_id=DEV_USER.id)
        db.add(report)
        db.commit()
        db.refresh(report)
        report_id = report.id
    finally:
        db.close()


    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    try:
        resp = client.patch(
            f"{PREFIX}/{report_id}",
            json={"description": "Тест: обид за промена."},
        )
        assert resp.status_code == 403
        assert "not allowed" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_13_officer_can_see_all_reports(client: TestClient):
    created = _create(client, {"description": "Officer тест: листање."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: OFFICER_USER
    try:
        resp = client.get(PREFIX)
        assert resp.status_code == 200
        assert report_id in [r["id"] for r in resp.json()], "Officer не го гледа репортот"
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_14_create_report_max_length_description(client: TestClient):
    valid_desc   = "Долг опис: " + "а" * 4989   # точно 5000 знаци
    invalid_desc = "Долг опис: " + "а" * 4990   # 5001 — премногу
    assert client.post(PREFIX, json={"description": valid_desc}).status_code == 201
    assert client.post(PREFIX, json={"description": invalid_desc}).status_code == 422


def test_15_patch_nonexistent_report_returns_404(client: TestClient):
    resp = client.patch(
        f"{PREFIX}/999999",
        json={"description": "Тест: patch на непостоечки."},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()

