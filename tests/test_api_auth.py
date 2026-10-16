from fastapi.testclient import TestClient

from open_invoice_engine.main import app


def test_health_check_stays_public_when_api_key_is_enabled(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret")
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_routes_require_configured_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-secret")
    client = TestClient(app)

    unauthorized = client.post("/validate", json={})
    assert unauthorized.status_code == 401

    authorized = client.post(
        "/validate",
        json={},
        headers={"X-API-Key": "test-secret"},
    )
    # Authentication passed; the empty payload is rejected by schema validation.
    assert authorized.status_code == 422
