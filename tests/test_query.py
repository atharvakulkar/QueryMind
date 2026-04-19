"""Tests for demo dataset and gated ad-hoc SQL."""

from fastapi.testclient import TestClient

from backend.main import create_app
from core.config import Settings
from tests.conftest import FakeConnectionManager


def test_demo_dataset(test_settings: Settings, fake_cm: FakeConnectionManager) -> None:
    app = create_app(settings=test_settings, connection_manager=fake_cm)
    with TestClient(app) as client:
        response = client.get("/api/v1/demo/dataset")
    assert response.status_code == 200
    body = response.json()
    assert body["columns"]
    assert body["rows"]
    assert "execution_time_ms" in body


def test_adhoc_sql_disabled_by_default(
    test_settings: Settings,
    fake_cm: FakeConnectionManager,
) -> None:
    app = create_app(settings=test_settings, connection_manager=fake_cm)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/internal/execute-read",
            json={"sql": "SELECT 1"},
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "adhoc_sql_disabled"


def test_adhoc_sql_allowed_with_select(
    fake_cm: FakeConnectionManager,
) -> None:
    settings = Settings.model_validate(
        {
            "database_url": "postgresql://user:pass@127.0.0.1:65432/querymind_test",
            "allow_adhoc_sql": True,
        },
    )
    fake_cm.fetch_result = (["one"], [{"one": 1}], 0.001)
    app = create_app(settings=settings, connection_manager=fake_cm)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/internal/execute-read",
            json={"sql": "SELECT 1 AS one"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["rows"][0]["one"] == 1
