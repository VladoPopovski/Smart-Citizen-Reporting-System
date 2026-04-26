"""
E2E Integration Tests — /api/v1/reports
=========================================
Вкупно: 25 тестови (15 оригинални + 10 нови E2E)

Нови E2E тестови покриваат:
  - Citizen workflow со lat/lng + verify во DB
  - Status timeline (history_entries)
  - Officer коментари видливи за citizen
  - CSV export
  - Analytics summary
  - Duplicate detection

Стартување:
  python -m pytest tests/test_reports_api.py -v
  python -m pytest tests/test_reports_api.py -v --cov=app --cov-report=term-missing
"""

from __future__ import annotations

import csv
import io
import os
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ── Мора да биде ПРЕД сите app imports ────────────────────────────────────────
os.environ["DEV_SKIP_AUTH"] = "true"
os.environ["AI_ENABLED"] = "false"        # ← додај ова
os.environ["AI_PRELOAD_ON_STARTUP"] = "false"  # ← и ова

from app.core.config import get_settings        # noqa: E402
get_settings.cache_clear()

from app.db.session import SessionLocal         # noqa: E402
from app.main import app                        # noqa: E402
from app.models.report import Report            # noqa: E402
from app.schemas.user import CurrentUser, UserRole  # noqa: E402
from app.utils.dependencies import DEV_USER, get_current_user  # noqa: E402

# ── Константи ─────────────────────────────────────────────────────────────────
PREFIX          = "/api/v1/reports"
ANALYTICS_PREFIX = "/api/v1/analytics"
DEV_USER_ID     = str(DEV_USER.id)  # "12345678-1234-1234-1234-123456789012"

# Citizen — UUID кој НЕ постои во users (само за get_current_user override)
CITIZEN_USER = CurrentUser(
    id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    email="citizen_test@example.com",
    role=UserRole.citizen,
)

# Officer — UUID кој постои во users табела
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
    "E2E%",
    "Дупликат%",
]


# ── run_all_tests ─────────────────────────────────────────────────────────────

def run_all_tests():
    """Ги рандира сите тестови еден по еден со pytest."""
    import pytest as _pytest
    tests = [
        f"tests/test_reports_api.py::{name}"
        for name in [
            "test_01_create_report_minimal_payload",
            "test_02_create_report_with_location",
            "test_03_create_report_empty_description_fails",
            "test_04_create_report_missing_description_fails",
            "test_05_list_reports_admin_sees_all",
            "test_06_get_report_by_id",
            "test_07_get_report_not_found",
            "test_08_patch_report_description",
            "test_09_patch_admin_can_change_status_and_category",
            "test_10_delete_report",
            "test_11_get_report_forbidden_for_citizen",
            "test_12_citizen_cannot_patch_foreign_report",
            "test_13_officer_can_see_all_reports",
            "test_14_create_report_max_length_description",
            "test_15_patch_nonexistent_report_returns_404",
            "test_16_citizen_submit_report_with_location_verified_in_db",
            "test_17_citizen_cannot_see_foreign_report",
            "test_18_status_timeline_recorded_on_patch",
            "test_19_officer_post_comment_citizen_sees_it",
            "test_20_officer_export_csv_valid",
            "test_21_analytics_summary_returns_expected_keys",
            "test_22_duplicate_detection_sets_flag",
            "test_23_report_create_with_title",
            "test_24_patch_status_endpoint_officer",
            "test_25_citizen_list_sees_only_own_reports",
        ]
    ]
    for test in tests:
        print(f"\n{'='*60}\nРандирам: {test}\n{'='*60}")
        _pytest.main([test, "-v", "--no-header"])


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Admin client (DEV_USER) — постои во users табела."""
    app.dependency_overrides[get_current_user] = lambda: DEV_USER
    with TestClient(app) as c:
        yield c
    app.dependency_overrides[get_current_user] = lambda: DEV_USER


@pytest.fixture(autouse=True)
def cleanup_reports():
    """Брише тест-репорти по секој тест за изолација."""
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
    """Помошник: POST нов репорт и врати response JSON."""
    resp = client.post(PREFIX, json=payload or VALID_PAYLOAD)
    assert resp.status_code == 201, f"Неуспешно креирање: {resp.text}"
    return resp.json()


# ═════════════════════════════════════════════════════════════════════════════
# ОРИГИНАЛНИ 15 ТЕСТОВИ
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
    valid_desc   = "Долг опис: " + "а" * 4989
    invalid_desc = "Долг опис: " + "а" * 4990
    assert client.post(PREFIX, json={"description": valid_desc}).status_code == 201
    assert client.post(PREFIX, json={"description": invalid_desc}).status_code == 422


def test_15_patch_nonexistent_report_returns_404(client: TestClient):
    resp = client.patch(
        f"{PREFIX}/999999",
        json={"description": "Тест: patch на непостоечки."},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ═════════════════════════════════════════════════════════════════════════════
# НОВИ E2E ТЕСТОВИ
# ═════════════════════════════════════════════════════════════════════════════

def test_16_citizen_submit_report_with_location_verified_in_db(client: TestClient):
    """
    E2E: Citizen submit report со lat/lng.
    Проверуваме дека координатите се зачувани точно во DB.
    """
    payload = {
        "description": "E2E: Оштетен тротоар со прецизна локација.",
        "latitude": 41.9981,
        "longitude": 21.4254,
    }
    resp = client.post(PREFIX, json=payload)
    assert resp.status_code == 201
    report_id = resp.json()["id"]

    # Verify директно во DB
    db: Session = SessionLocal()
    try:
        report = db.get(Report, report_id)
        assert report is not None
        assert report.description == payload["description"]
        assert report.latitude == pytest.approx(41.9981)
        assert report.longitude == pytest.approx(21.4254)
        assert str(report.user_id) == DEV_USER_ID
    finally:
        db.close()


def test_17_citizen_cannot_see_foreign_report(client: TestClient):
    """
    E2E: Citizen не може да го вчита репортот на друг корисник.
    Репортот е на DEV_USER (admin), citizen добива 403.
    """
    created = _create(client, {"description": "E2E: Репорт на admin, citizen го бара."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    try:
        resp = client.get(f"{PREFIX}/{report_id}")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_18_status_timeline_recorded_on_patch(client: TestClient):
    """
    E2E: Кога admin го менува status_id преку PATCH,
    history_entries во response мора да содржи запис со новиот status.
    """
    created = _create(client, {"description": "E2E: Status timeline тест."})
    report_id = created["id"]

    # Прв status change
    resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": 1})
    assert resp.status_code == 200
    body = resp.json()

    assert "history_entries" in body
    assert len(body["history_entries"]) >= 1
    statuses = [h["status_id"] for h in body["history_entries"]]
    assert 1 in statuses


def test_19_officer_post_comment_citizen_sees_it(client: TestClient):
    """
    E2E: Officer додава коментар на репорт.
    Кога admin го вчитува репортот, коментарот е видлив во comments листата.
    """
    created = _create(client, {"description": "E2E: Репорт за коментар."})
    report_id = created["id"]

    # Officer додава коментар
    app.dependency_overrides[get_current_user] = lambda: OFFICER_USER
    try:
        comment_resp = client.post(
            f"{PREFIX}/{report_id}/comments",
            json={"content": "E2E: Офицерски коментар — потврдено на терен."},
        )
        assert comment_resp.status_code == 201, f"Comment failed: {comment_resp.text}"
        comment_id = comment_resp.json()["id"]
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER

    # Admin го вчитува репортот и го гледа коментарот
    get_resp = client.get(f"{PREFIX}/{report_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert "comments" in body
    comment_ids = [c["id"] for c in body["comments"]]
    assert comment_id in comment_ids


def test_20_officer_export_csv_valid(client: TestClient):
    """
    E2E: GET /analytics/export/csv враќа валиден CSV.
    Проверуваме: Content-Type, HTTP 200, header row постои.
    """
    # Треба admin за analytics
    resp = client.get(f"{ANALYTICS_PREFIX}/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")

    content = resp.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) >= 1, "CSV мора да содржи барем header row"

    header = rows[0]
    assert "ID" in header
    assert "Description" in header


def test_21_analytics_summary_returns_expected_keys(client: TestClient):
    """
    E2E: GET /analytics/summary враќа очекувана структура.
    Проверуваме дека сите клучни полиња постојат во response.
    """
    resp = client.get(f"{ANALYTICS_PREFIX}/summary")
    assert resp.status_code == 200

    body = resp.json()
    assert "kpis" in body
    assert "categoryData" in body
    assert "pieData" in body
    assert "monthlyData" in body
    assert "resolutionRate" in body

    kpis = body["kpis"]
    assert "total" in kpis
    assert "resolved" in kpis
    assert "avgTime" in kpis
    assert "activeCitizens" in kpis


def test_22_duplicate_detection_sets_flag(client: TestClient):
    """
    E2E: Два идентични репорти со иста локација.
    Вториот мора да добие possible_duplicate_of != None.
    """
    payload = {
        "description": "E2E: Дупликат — расипан хидрант на главната улица.",
        "latitude": 41.9950,
        "longitude": 21.4300,
    }

    first = _create(client, payload)
    first_id = first["id"]

    second_resp = client.post(PREFIX, json=payload)
    assert second_resp.status_code == 201
    second = second_resp.json()

    assert second["possible_duplicate_of"] == first_id, (
        f"Вториот репорт мора да го флагира прво: {first_id}, "
        f"доби: {second['possible_duplicate_of']}"
    )


def test_23_report_create_with_title(client: TestClient):
    """
    E2E: ReportCreate поддржува опционален title.
    Проверуваме дека title се зачувува и се враќа во response.
    """
    payload = {
        "title": "E2E: Наслов на репорт",
        "description": "E2E: Детален опис со наслов.",
    }
    resp = client.post(PREFIX, json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "E2E: Наслов на репорт"


def test_24_patch_status_endpoint_officer(client: TestClient):
    """
    E2E: PATCH /{id}/status е посебен endpoint само за officer/admin.
    Officer го менува status_id и history се логира.
    """
    created = _create(client, {"description": "E2E: Status endpoint тест."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: OFFICER_USER
    try:
        resp = client.patch(
            f"{PREFIX}/{report_id}/status",
            json={"status_id": 1},
        )
        assert resp.status_code == 200, f"Status patch failed: {resp.text}"
        body = resp.json()
        assert body["status_id"] == 1
        assert len(body["history_entries"]) >= 1
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_25_citizen_list_sees_only_own_reports(client: TestClient):
    """
    E2E: Citizen го листа само своите репорти.
    Во базата постои репорт на DEV_USER (admin) — citizen НЕ смее да го гледа.
    Citizen нема свои репорти → листата мора да е празна.
    """
    # Креирај репорт со admin (DEV_USER)
    _create(client, {"description": "E2E: Admin репорт, citizen не гo гледа."})

    # Citizen листа — мора да добие само свои (нула)
    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    try:
        resp = client.get(PREFIX)
        assert resp.status_code == 200
        reports = resp.json()
        # Сите репорти мора да имаат user_id == CITIZEN_USER.id
        for r in reports:
            assert r["user_id"] == str(CITIZEN_USER.id), (
                f"Citizen доби туѓ репорт: {r['user_id']}"
            )
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_26_officer_can_patch_priority(client: TestClient):
    created = _create(client, {"description": "E2E: priority patch by officer."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: OFFICER_USER
    try:
        resp = client.patch(
            f"{PREFIX}/{report_id}/priority",
            json={"priority": "Итен"},
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "Итен"
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


def test_27_citizen_cannot_patch_priority(client: TestClient):
    created = _create(client, {"description": "E2E: citizen cannot patch priority."})
    report_id = created["id"]

    app.dependency_overrides[get_current_user] = lambda: CITIZEN_USER
    try:
        resp = client.patch(
            f"{PREFIX}/{report_id}/priority",
            json={"priority": "Висок"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = lambda: DEV_USER


if __name__ == "__main__":
    run_all_tests()
