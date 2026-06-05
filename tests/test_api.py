from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["storage_backend"] == "local"


def test_analyze_endpoint_accepts_pdf_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/analyze",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"]
    assert "risk_score" in body
    assert "recommendation" in body

