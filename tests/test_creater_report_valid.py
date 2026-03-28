from fastapi.testclient import TestClient
from uuid import UUID

from app.main import app
from app.schemas.user import CurrentUser, UserRole
from app.utils.dependencies import require_roles


fake_user = CurrentUser(
    id=UUID("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
    email="user@example.com",
    role=UserRole.citizen
)


def override_require_roles(*roles):
    return fake_user

app.dependency_overrides[require_roles] = override_require_roles

client = TestClient(app)

API_PREFIX = "/api/v1"


def test_create_report_valid():
    payload = {
        "description": "Test report",
        "latitude": 41.9981,
        "longitude": 21.4254
    }
    response = client.post(f"{API_PREFIX}/reports", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Test report"
    assert data["user_id"] == str(fake_user.id)
