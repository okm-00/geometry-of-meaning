"""
Integration tests for app/main.py.

generate_story() is mocked at the import boundary — no real LLM calls are made.
LM Studio connectivity is also mocked for health endpoint tests.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.story import StoryResult, LLMConnectionError, LLMResponseError, LLMParseError

client = TestClient(app)

VALID_RESULT = StoryResult(
    body=["Para one.", "Para two.", "Para three."],
    endings=["Ending A.", "Ending B."],
)


# ---------------------------------------------------------------------------
# POST /api/story
# ---------------------------------------------------------------------------

@patch("app.main.generate_story", return_value=VALID_RESULT)
def test_story_success(_mock):
    response = client.post("/api/story")
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == VALID_RESULT.body
    assert data["endings"] == VALID_RESULT.endings


@patch("app.main.generate_story", side_effect=LLMConnectionError("LM Studio unreachable"))
def test_story_connection_error_returns_503(_mock):
    response = client.post("/api/story")
    assert response.status_code == 503
    assert "detail" in response.json()


@patch("app.main.generate_story", side_effect=LLMResponseError("HTTP 404"))
def test_story_response_error_returns_502(_mock):
    response = client.post("/api/story")
    assert response.status_code == 502
    assert "detail" in response.json()


@patch("app.main.generate_story", side_effect=LLMParseError("not valid JSON"))
def test_story_parse_error_returns_502(_mock):
    response = client.post("/api/story")
    assert response.status_code == 502
    assert "detail" in response.json()


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@patch("app.main.OpenAI")
def test_health_reachable(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.return_value = []

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["lm_studio"] == "reachable"


@patch("app.main.OpenAI")
def test_health_unreachable(mock_openai_cls):
    from openai import APIConnectionError
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.side_effect = APIConnectionError(request=MagicMock())

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["lm_studio"] == "unreachable"
    assert "detail" in data
