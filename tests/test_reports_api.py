"""
API Integration Tests — /api/v1/reports
=========================================
Вкупно: 15 тестови

Барања:
  - PostgreSQL база да е стартувана: docker compose up -d
  - Seed да е применет:             python scripts/seed.py
  - app/services/report_service.py  да е заменет со report_service_fixed.py

Стартување:
  python -m pytest tests/test_reports_api.py -v
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ── Environment variables ПРЕД app imports ───────────────────────────────────
os.environ["DEV_SKIP_AUTH"] = "true"
os.environ["AI_ENABLED"] = "false"

from app.core.config import get_settings
get_settings.cache_clear()

from app.db.session import SessionLocal
from app.main import app
from app.models.history import History
from app.models.report import Report
from app.schemas.user import CurrentUser, UserRole
from app.utils.dependencies import get_current_user

# ── Константи ─────────────────────────────────────────────────────────────────

PREFIX = "/api/v1/reports"

# Seeded корисници — мора да се совпаѓаат со scripts/seed.py
CITIZEN_ID = uuid.UUID("12345678-1234-1234-1234-123456789012")
OFFICER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_ID   = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

CITIZEN_USER = CurrentUser(id=CITIZEN_ID, email="citizen@example.com", role=UserRole.citizen)
OFFICER_USER = CurrentUser(id=OFFICER_ID, email="officer@example.com", role=UserRole.officer)
ADMIN_USER   = CurrentUser(id=ADMIN_ID,   email="admin@example.com",   role=UserRole.admin)

# Seeded ID-а — види scripts/seed.py
STATUS_SUBMITTED   = 1
STATUS_IN_PROGRESS = 2
STATUS_RESOLVED    = 3
CATEGORY_INFRA     = 1

VALID_PAYLOAD = {"description": "Тест: скршена улична светилка кај плоштадот."}
_CLEANUP_PREFIX = "Тест:%"


# ── Helpers ───────────────────────────────────────────────────────────────────

@contextmanager
def override_user(user: CurrentUser):
    """
    Thread-safe context manager за промена на dependency_overrides.
    Гарантира дека override се враќа назад дури и при exception.
    """
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield
    finally:
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER


def create_report_as(client: TestClient, user: CurrentUser, payload: dict | None = None) -> dict:
    """
    Креира репорт во контекст на даден корисник.

    FIX T06: Officer не може да POST /reports — рутерот дозволува само citizen/admin.
    За officer, создаваме преку admin и го менуваме user_id директно во DB.
    """
    p = payload or VALID_PAYLOAD

    if user.role == UserRole.officer:
        # Officer не смее да POST — создај преку admin, потоа смени user_id во DB
        with override_user(ADMIN_USER):
            resp = client.post(PREFIX, json=p)
        assert resp.status_code == 201, f"Неуспешно креирање (admin proxy за officer): {resp.text}"
        report_data = resp.json()

        db: Session = SessionLocal()
        try:
            report = db.get(Report, report_data["id"])
            report.user_id = user.id
            db.commit()
            db.refresh(report)
            report_data["user_id"] = str(report.user_id)
        finally:
            db.close()

        return report_data

    with override_user(user):
        resp = client.post(PREFIX, json=p)
    assert resp.status_code == 201, f"Неуспешно креирање: {resp.text}"
    return resp.json()


def get_history_for_report(report_id: int) -> list[History]:
    """Директно чита History записи од DB за даден report_id."""
    db: Session = SessionLocal()
    try:
        return db.query(History).filter(History.report_id == report_id).all()
    finally:
        db.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    TestClient со ADMIN_USER по default.

    FIX T08: raise_server_exceptions=False — TestClient НЕ ги пропагира
    server-side exceptions (IntegrityError) како Python exceptions.
    Наместо тоа, добиваме HTTP response со status_code=500.
    """
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER


@pytest.fixture(autouse=True)
def cleanup_reports():
    """Брише сите test репорти по секој тест."""
    yield
    db: Session = SessionLocal()
    try:
        db.query(Report).filter(Report.description.like(_CLEANUP_PREFIX)).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# T01 — Citizen НЕ може да го смени status_id (статусот останува NULL)
# ═══════════════════════════════════════════════════════════════════════════════

def test_t01_citizen_cannot_change_status(client: TestClient):
    """
    Сценарио: Citizen се обидува да го смени status_id на свој репорт.
    Очекување: 200 се враќа, НО status_id НЕ се менува (сервисот го игнорира).
    Статус кодови: 200
    """
    report = create_report_as(client, CITIZEN_USER, {"description": "Тест: citizen status attempt."})
    report_id = report["id"]
    assert report["status_id"] is None

    with override_user(CITIZEN_USER):
        resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": STATUS_SUBMITTED})

    assert resp.status_code == 200, f"Очекувано 200, добиено: {resp.status_code}"
    assert resp.json()["status_id"] is None, (
        "Citizen не смее да го смени status_id — треба да остане NULL"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T02 — Officer МОЖЕ да го смени status (200)
# ═══════════════════════════════════════════════════════════════════════════════

def test_t02_officer_can_change_status(client: TestClient):
    """
    Сценарио: Officer го менува status_id на репорт.
    Очекување: 200 + status_id е ажуриран.
    Статус кодови: 200
    """
    report = create_report_as(client, ADMIN_USER, {"description": "Тест: officer status change."})
    report_id = report["id"]

    with override_user(OFFICER_USER):
        resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": STATUS_IN_PROGRESS})

    assert resp.status_code == 200, f"Officer треба да може да смени статус: {resp.text}"
    assert resp.json()["status_id"] == STATUS_IN_PROGRESS


# ═══════════════════════════════════════════════════════════════════════════════
# T03 — Admin МОЖЕ да го смени status (200)
# ═══════════════════════════════════════════════════════════════════════════════

def test_t03_admin_can_change_status(client: TestClient):
    """
    Сценарио: Admin го менува status_id и category_id на репорт.
    Очекување: 200 + двете полиња се ажурирани.
    Статус кодови: 200
    """
    report = create_report_as(client, ADMIN_USER, {"description": "Тест: admin status change."})
    report_id = report["id"]

    with override_user(ADMIN_USER):
        resp = client.patch(
            f"{PREFIX}/{report_id}",
            json={"status_id": STATUS_RESOLVED, "category_id": CATEGORY_INFRA},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status_id"] == STATUS_RESOLVED
    assert body["category_id"] == CATEGORY_INFRA


# ═══════════════════════════════════════════════════════════════════════════════
# T04 — При промена на статус се креира History запис
# ═══════════════════════════════════════════════════════════════════════════════

def test_t04_status_change_creates_history_record(client: TestClient):
    """
    Сценарио: Officer го менува статусот — очекуваме History запис во DB.
    Очекување: 200 + 1 History запис со точен status_id и changed_by_user_id.

    ПРЕДУСЛОВ: app/services/report_service.py мора да е заменет со
    report_service_fixed.py — ако паѓа со '0 != 1', сè уште го користиш старото!

    Статус кодови: 200
    """
    report = create_report_as(client, ADMIN_USER, {"description": "Тест: history tracking."})
    report_id = report["id"]

    with override_user(OFFICER_USER):
        resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": STATUS_IN_PROGRESS})

    assert resp.status_code == 200

    history = get_history_for_report(report_id)
    assert len(history) == 1, (
        f"Очекуван 1 History запис, добиени: {len(history)}\n"
        "АКЦИЈА: Замени app/services/report_service.py со report_service_fixed.py!"
    )
    assert history[0].status_id == STATUS_IN_PROGRESS
    assert history[0].changed_by_user_id == OFFICER_ID


# ═══════════════════════════════════════════════════════════════════════════════
# T05 — Citizen ги гледа само своите репорти
# ═══════════════════════════════════════════════════════════════════════════════

def test_t05_citizen_sees_only_own_reports(client: TestClient):
    """
    Сценарио: Admin и Citizen имаат различни репорти. Citizen го листа /reports.
    Очекување: Citizen гледа само свои репорти, НЕ ги гледа admin репортите.
    Статус кодови: 200
    """
    admin_report   = create_report_as(client, ADMIN_USER,   {"description": "Тест: admin репорт."})
    citizen_report = create_report_as(client, CITIZEN_USER, {"description": "Тест: citizen репорт."})

    with override_user(CITIZEN_USER):
        resp = client.get(PREFIX)

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert citizen_report["id"] in ids,     "Citizen треба да го гледа сопствениот репорт"
    assert admin_report["id"] not in ids,   "Citizen НЕ смее да го гледа admin репортот"

    for r in resp.json():
        assert r["user_id"] == str(CITIZEN_ID), f"Citizen гледа туѓ репорт! user_id={r['user_id']}"


# ═══════════════════════════════════════════════════════════════════════════════
# T06 — Officer и Admin ги гледаат сите репорти
# ═══════════════════════════════════════════════════════════════════════════════

def test_t06_officer_and_admin_see_all_reports(client: TestClient):
    """
    Сценарио: Citizen и Officer имаат репорти. Officer и Admin ги листаат сите.

    FIX: create_report_as() го решава проблемот дека officer не може да POST —
    создава преку admin и го менува user_id во DB.

    Статус кодови: 200
    """
    citizen_report = create_report_as(client, CITIZEN_USER, {"description": "Тест: видливост citizen."})
    officer_report = create_report_as(client, OFFICER_USER, {"description": "Тест: видливост officer."})

    for user, label in [(OFFICER_USER, "Officer"), (ADMIN_USER, "Admin")]:
        with override_user(user):
            resp = client.get(PREFIX)
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert citizen_report["id"] in ids, f"{label} треба да го гледа citizen репортот"
        assert officer_report["id"] in ids, f"{label} треба да го гледа officer репортот"


# ═══════════════════════════════════════════════════════════════════════════════
# T07 — Citizen добива 403 при GET /{id} на туѓ репорт
# ═══════════════════════════════════════════════════════════════════════════════

def test_t07_citizen_cannot_get_foreign_report(client: TestClient):
    """
    Сценарио: Admin креира репорт. Citizen се обидува да го земе по ID.
    Очекување: 403 Forbidden.
    Статус кодови: 403
    """
    admin_report = create_report_as(client, ADMIN_USER, {"description": "Тест: туѓ за citizen GET."})
    report_id = admin_report["id"]

    with override_user(CITIZEN_USER):
        resp = client.get(f"{PREFIX}/{report_id}")

    assert resp.status_code == 403
    assert "not allowed" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# T08 — PATCH со непостоечки status_id враќа 500 (FK violation)
# ═══════════════════════════════════════════════════════════════════════════════

def test_t08_patch_with_invalid_status_id(client: TestClient):
    """
    Сценарио: Admin се обидува да постави status_id=99999 (не постои во DB).
    Очекување: 500 — PostgreSQL фрла ForeignKeyViolation.

    FIX: client fixture користи raise_server_exceptions=False,
    па IntegrityError се враќа како HTTP 500 наместо Python exception crash.

    Статус кодови: 500
    """
    report = create_report_as(client, ADMIN_USER, {"description": "Тест: invalid status_id."})
    report_id = report["id"]

    with override_user(ADMIN_USER):
        resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": 99999})

    assert resp.status_code == 500, (
        f"Очекуван 500 (FK violation), добиен: {resp.status_code} — {resp.text[:200]}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T09 — Citizen не може да смени status_id дури и на свој репорт
# ═══════════════════════════════════════════════════════════════════════════════

def test_t09_citizen_cannot_change_own_report_status(client: TestClient):
    """
    Сценарио: Citizen се обидува да го смени статусот на СВОЈ репорт.
    Очекување: 200, НО status_id останува NULL. Нема History запис.
    Статус кодови: 200
    """
    report = create_report_as(client, CITIZEN_USER, {"description": "Тест: citizen own status."})
    report_id = report["id"]
    assert report["status_id"] is None

    with override_user(CITIZEN_USER):
        resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": STATUS_SUBMITTED})

    assert resp.status_code == 200
    assert resp.json()["status_id"] is None, (
        "Citizen не смее да го смени status_id дури и на сопствен репорт"
    )
    assert len(get_history_for_report(report_id)) == 0, (
        "Не треба History запис кога citizen се обидува да смени статус"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T10 — Повеќекратна промена на статус → History расте
# ═══════════════════════════════════════════════════════════════════════════════

def test_t10_multiple_status_changes_create_multiple_history_records(client: TestClient):
    """
    Сценарио: Admin го менува статусот 3 пати по ред.
    Очекување: По секоја промена History листата расте за 1.

    ПРЕДУСЛОВ: report_service_fixed.py мора да е на место.

    Статус кодови: 200 × 3
    """
    report = create_report_as(client, ADMIN_USER, {"description": "Тест: multiple status changes."})
    report_id = report["id"]

    status_sequence = [STATUS_SUBMITTED, STATUS_IN_PROGRESS, STATUS_RESOLVED]

    for i, status_id in enumerate(status_sequence, start=1):
        with override_user(ADMIN_USER):
            resp = client.patch(f"{PREFIX}/{report_id}", json={"status_id": status_id})
        assert resp.status_code == 200

        history = get_history_for_report(report_id)
        assert len(history) == i, (
            f"По {i}. промена, очекувани {i} History записи, добиени {len(history)}\n"
            "АКЦИЈА: Замени app/services/report_service.py со report_service_fixed.py!"
        )

    history = get_history_for_report(report_id)
    recorded = [h.status_id for h in sorted(history, key=lambda h: h.created_at)]
    assert recorded == status_sequence, (
        f"History редослед не се совпаѓа: {recorded} != {status_sequence}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T11 — Officer може да го види туѓ репорт (GET /{id})
# ═══════════════════════════════════════════════════════════════════════════════

def test_t11_officer_can_get_any_report(client: TestClient):
    """
    Сценарио: Citizen креира репорт. Officer го зема по ID.
    Очекување: 200 + точен report_id.
    Статус кодови: 200
    """
    citizen_report = create_report_as(
        client, CITIZEN_USER, {"description": "Тест: officer read citizen report."}
    )
    report_id = citizen_report["id"]

    with override_user(OFFICER_USER):
        resp = client.get(f"{PREFIX}/{report_id}")

    assert resp.status_code == 200
    assert resp.json()["id"] == report_id


# ═══════════════════════════════════════════════════════════════════════════════
# T12 — Citizen може да ги ажурира description/location на сопствен репорт
# ═══════════════════════════════════════════════════════════════════════════════

def test_t12_citizen_can_update_own_description_and_location(client: TestClient):
    """
    Сценарио: Citizen ги менува description и координатите на свој репорт.
    Очекување: 200 + ажурирани полиња; status/category останува NULL.
    Статус кодови: 200
    """
    report = create_report_as(
        client, CITIZEN_USER,
        {"description": "Тест: citizen update own.", "latitude": 41.99, "longitude": 21.43},
    )
    report_id = report["id"]

    with override_user(CITIZEN_USER):
        resp = client.patch(
            f"{PREFIX}/{report_id}",
            json={"description": "Тест: citizen update own — ажуриран.", "latitude": 42.00, "longitude": 21.44},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "Тест: citizen update own — ажуриран."
    assert body["latitude"]  == pytest.approx(42.00)
    assert body["longitude"] == pytest.approx(21.44)
    assert body["status_id"]   is None
    assert body["category_id"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# T13 — Citizen НЕ може да patch туѓ репорт (403)
# ═══════════════════════════════════════════════════════════════════════════════

def test_t13_citizen_cannot_patch_foreign_report(client: TestClient):
    """
    Сценарио: Admin креира репорт. Citizen се обидува да го ажурира.
    Очекување: 403 Forbidden.
    Статус кодови: 403
    """
    admin_report = create_report_as(client, ADMIN_USER, {"description": "Тест: туѓ за citizen PATCH."})
    report_id = admin_report["id"]

    with override_user(CITIZEN_USER):
        resp = client.patch(
            f"{PREFIX}/{report_id}",
            json={"description": "Тест: обид за неовластена промена."},
        )

    assert resp.status_code == 403
    assert "not allowed" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# T14 — GET /reports враќа 200 со листа за admin
# ═══════════════════════════════════════════════════════════════════════════════

def test_t14_admin_list_reports_returns_200(client: TestClient):
    """
    Сценарио: Admin листа /reports по креирање на 2 репорти.
    Очекување: 200 + двата репорти присутни + задолжителни полиња.
    Статус кодови: 200
    """
    r1 = create_report_as(client, ADMIN_USER,   {"description": "Тест: list check 1."})
    r2 = create_report_as(client, CITIZEN_USER, {"description": "Тест: list check 2."})

    with override_user(ADMIN_USER):
        resp = client.get(PREFIX)

    assert resp.status_code == 200
    ids = [r["id"] for r in resp.json()]
    assert r1["id"] in ids
    assert r2["id"] in ids

    for report in resp.json():
        for field in ("id", "description", "user_id", "created_at"):
            assert field in report, f"Поле '{field}' недостасува во response"


# ═══════════════════════════════════════════════════════════════════════════════
# T15 — PATCH на непостоечки репорт враќа 404
# ═══════════════════════════════════════════════════════════════════════════════

def test_t15_patch_nonexistent_report_returns_404(client: TestClient):
    """
    Сценарио: Admin се обидува да patch репорт со ID=999999 (не постои).
    Очекување: 404 + "not found" во detail.
    Статус кодови: 404
    """
    with override_user(ADMIN_USER):
        resp = client.patch(
            f"{PREFIX}/999999",
            json={"description": "Тест: patch непостоечки."},
        )

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()