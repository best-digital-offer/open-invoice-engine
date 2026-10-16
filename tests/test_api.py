from fastapi.testclient import TestClient

from open_invoice_engine.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_extract_rejects_non_pdf():
    response = client.post(
        "/extract",
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 415


def test_validate_endpoint():
    response = client.post(
        "/validate",
        json={
            "invoice_number": "INV-1",
            "invoice_date": "2026-10-16",
            "currency": "USD",
            "subtotal": 100,
            "tax": 8,
            "discount": 0,
            "total": 108,
        },
    )
    assert response.status_code == 200
    assert response.json()["valid"] is True
