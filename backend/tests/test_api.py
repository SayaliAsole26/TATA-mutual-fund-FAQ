"""Tests for FastAPI endpoints (Phase 2c)."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "index" in body
    assert "llm" in body
    assert body["llm"]["provider"] == "groq"
    assert "configured" in body["llm"]


def test_schemes_endpoint() -> None:
    response = client.get("/api/schemes")
    assert response.status_code == 200
    body = response.json()
    assert body["amc"] == "Tata Mutual Fund"
    assert len(body["schemes"]) == 15


def test_chat_clarification() -> None:
    response = client.post("/api/chat", json={"message": "What is the expense ratio?"})
    assert response.status_code == 200
    assert response.json()["type"] == "clarification"


@patch("app.api.chat.handle_chat")
def test_chat_answer_mock(mock_handle) -> None:
    mock_handle.return_value = {
        "type": "answer",
        "answer": "The expense ratio is 1.17%.\n\nSource: https://groww.in/mutual-funds/tata-elss-fund-direct-growth\n\nLast updated from sources: 18 Jun 2026",
        "scheme_id": "tata-elss-fund-direct-growth",
        "scheme_name": "Tata ELSS Fund Direct Growth",
        "source_url": "https://groww.in/mutual-funds/tata-elss-fund-direct-growth",
        "last_updated": "2026-06-18T18:09:51+00:00",
        "sections_used": ["expense_ratio"],
        "retrieval_source": "structured",
    }
    response = client.post(
        "/api/chat",
        json={"message": "What is the expense ratio of Tata ELSS?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "answer"
    assert "1.17%" in body["answer"]


def test_cors_allows_vercel_preview_origin() -> None:
    origin = "https://tata-mutual-fund-faq-git-main-sayaliasole26.vercel.app"
    response = client.options(
        "/api/chat",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
