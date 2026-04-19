"""Tests for health and readiness routes."""

from fastapi.testclient import TestClient

from backend.main import create_app
from core.config import Settings
from tests.conftest import FakeConnectionManager


def test_health_ok(test_settings: Settings, fake_cm: FakeConnectionManager) -> None:
    app = create_app(settings=test_settings, connection_manager=fake_cm)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "app_name" in body


def test_ready_success(test_settings: Settings, fake_cm: FakeConnectionManager) -> None:
    app = create_app(settings=test_settings, connection_manager=fake_cm)
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database_reachable"] is True


def test_ready_database_down(test_settings: Settings) -> None:
    bad_cm = FakeConnectionManager(healthy=False)
    app = create_app(settings=test_settings, connection_manager=bad_cm)
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "database_connection_error"
