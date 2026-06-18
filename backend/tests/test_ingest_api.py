"""Tests for admin ingest endpoint (Phase 3)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ingest_not_configured() -> None:
    with patch("app.api.ingest.get_settings") as mock_settings:
        mock_settings.return_value.ingest_api_key = ""
        response = client.post("/api/ingest", headers={"X-Admin-Key": "secret"})
    assert response.status_code == 503


def test_ingest_forbidden_without_key() -> None:
    with patch("app.api.ingest.get_settings") as mock_settings:
        mock_settings.return_value.ingest_api_key = "secret"
        response = client.post("/api/ingest")
    assert response.status_code == 403


@patch("app.api.ingest.subprocess.run")
def test_ingest_success(mock_run) -> None:
    mock_run.return_value = MagicMock(returncode=0, stderr="")
    with patch("app.api.ingest.get_settings") as mock_settings:
        mock_settings.return_value.ingest_api_key = "secret"
        response = client.post("/api/ingest", headers={"X-Admin-Key": "secret"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
