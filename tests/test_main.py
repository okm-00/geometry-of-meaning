"""
Integration tests for app/main.py.

generate_story() and all db functions are mocked — no LLM calls, no disk I/O.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.story import StoryResult, LLMConnectionError, LLMResponseError

client = TestClient(app)

# baseline: plain prose body, no endings (EndingStrategy.NONE)
_BASELINE = StoryResult(
    body=["Para one."],
    endings=[],
    condition="baseline",
    system_prompt="sys baseline",
    user_prompt="user baseline",
    timing_ms=100,
)

# harness: plain prose body, two harness-generated endings
_HARNESS = StoryResult(
    body=["Harness one."],
    endings=["Harness A.", "Harness B."],
    condition="harness",
    system_prompt="sys harness",
    user_prompt="user harness",
    timing_ms=200,
)


def _mock_generate(variant):
    return _BASELINE if variant.name == "baseline" else _HARNESS


# ---------------------------------------------------------------------------
# GET /api/variants
# ---------------------------------------------------------------------------

def test_get_variants_returns_200():
    response = client.get("/api/variants")
    assert response.status_code == 200


def test_get_variants_returns_baseline_and_harness():
    response = client.get("/api/variants")
    data = response.json()
    assert "variants" in data
    assert "baseline" in data["variants"]
    assert "harness" in data["variants"]


def test_get_variants_returns_dict_with_ending_strategy():
    response = client.get("/api/variants")
    data = response.json()
    assert isinstance(data["variants"], dict)
    assert "ending_strategy" in data["variants"]["baseline"]
    assert "ending_strategy" in data["variants"]["harness"]


def test_get_variants_returns_ending_strategies_list():
    response = client.get("/api/variants")
    data = response.json()
    assert "ending_strategies" in data
    assert isinstance(data["ending_strategies"], list)
    assert "none" in data["ending_strategies"]
    assert "harness" in data["ending_strategies"]


# ---------------------------------------------------------------------------
# POST /api/session
# ---------------------------------------------------------------------------

_SEL_BOTH = {"selections": [
    {"name": "baseline", "ending_strategy": "none"},
    {"name": "harness",  "ending_strategy": "harness"},
]}
_SEL_BASELINE = {"selections": [{"name": "baseline", "ending_strategy": "none"}]}
_SEL_HARNESS  = {"selections": [{"name": "harness",  "ending_strategy": "harness"}]}


@patch("app.main.db.save_session", return_value=7)
@patch("app.main.db.save_generation", side_effect=[13, 14])
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_success(_mock_gen, _mock_save_gen, _mock_save_sess):
    response = client.post("/api/session", json=_SEL_BOTH)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == 7
    by_condition = {g["condition"]: g for g in data["generations"]}
    assert by_condition["baseline"]["generation_id"] == 13
    assert by_condition["harness"]["generation_id"] == 14
    assert by_condition["baseline"]["body"] == _BASELINE.body
    assert by_condition["harness"]["body"] == _HARNESS.body
    assert by_condition["baseline"]["endings"] == _BASELINE.endings
    assert by_condition["harness"]["endings"] == _HARNESS.endings


@patch("app.main.db.save_session", return_value=1)
@patch("app.main.db.save_generation", side_effect=[1, 2])
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_response_has_no_extra_fields(_mock_gen, _mock_save_gen, _mock_save_sess):
    response = client.post("/api/session", json=_SEL_BOTH)
    data = response.json()
    assert set(data.keys()) == {"session_id", "generations"}
    assert len(data["generations"]) == 2
    for gen in data["generations"]:
        assert set(gen.keys()) == {"generation_id", "condition", "body", "endings"}


@patch("app.main.db.save_session", return_value=1)
@patch("app.main.db.save_generation", return_value=1)
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_single_variant(_mock_gen, _mock_save_gen, _mock_save_sess):
    response = client.post("/api/session", json=_SEL_BASELINE)
    assert response.status_code == 200
    data = response.json()
    assert len(data["generations"]) == 1
    assert data["generations"][0]["condition"] == "baseline"


def test_session_unknown_variant_returns_422():
    response = client.post(
        "/api/session",
        json={"selections": [{"name": "nonexistent"}]},
    )
    assert response.status_code == 422


def test_session_unknown_ending_strategy_returns_422():
    response = client.post(
        "/api/session",
        json={"selections": [{"name": "baseline", "ending_strategy": "bogus"}]},
    )
    assert response.status_code == 422


def test_session_missing_body_returns_422():
    response = client.post("/api/session")
    assert response.status_code == 422


def test_session_empty_selections_returns_422():
    response = client.post("/api/session", json={"selections": []})
    assert response.status_code == 422


def test_session_too_many_selections_returns_422():
    response = client.post(
        "/api/session",
        json={"selections": [
            {"name": "baseline"},
            {"name": "harness"},
            {"name": "baseline"},
        ]},
    )
    assert response.status_code == 422


@patch("app.main.generate_story", side_effect=LLMConnectionError("LM Studio unreachable"))
def test_session_lm_studio_down_returns_503(_mock):
    response = client.post("/api/session", json=_SEL_BOTH)
    assert response.status_code == 503
    assert "detail" in response.json()


@patch("app.main.generate_story", side_effect=LLMResponseError("HTTP 404"))
def test_session_response_error_returns_502(_mock):
    response = client.post("/api/session", json=_SEL_BOTH)
    assert response.status_code == 502
    assert "detail" in response.json()


@patch("app.main.db.save_session", return_value=1)
@patch("app.main.db.save_generation", return_value=1)
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_baseline_has_empty_endings(_mock_gen, _mock_save_gen, _mock_save_sess):
    """baseline variant returns empty endings list; endpoint must pass it through."""
    response = client.post("/api/session", json=_SEL_BASELINE)
    assert response.status_code == 200
    data = response.json()
    assert data["generations"][0]["endings"] == []


@patch("app.main.db.save_session", return_value=1)
@patch("app.main.db.save_generation", return_value=1)
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_harness_has_two_endings(_mock_gen, _mock_save_gen, _mock_save_sess):
    """harness variant returns two endings; endpoint must pass them through."""
    response = client.post("/api/session", json=_SEL_HARNESS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["generations"][0]["endings"]) == 2


@patch("app.main.db.save_session", return_value=1)
@patch("app.main.db.save_generation", return_value=1)
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_feature_override_ending_strategy(_mock_gen, _mock_save_gen, _mock_save_sess):
    """Overriding ending_strategy in the request is accepted (server applies dc_replace)."""
    response = client.post(
        "/api/session",
        json={"selections": [{"name": "baseline", "ending_strategy": "harness"}]},
    )
    assert response.status_code == 200


@patch("app.main.db.save_session", return_value=1)
@patch("app.main.db.save_generation", return_value=1)
@patch("app.main.generate_story", side_effect=_mock_generate)
def test_session_default_ending_strategy_accepted(_mock_gen, _mock_save_gen, _mock_save_sess):
    """Omitting ending_strategy in selections is valid (uses variant default)."""
    response = client.post(
        "/api/session",
        json={"selections": [{"name": "baseline"}]},
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/feedback
# ---------------------------------------------------------------------------

@patch("app.main.db.save_feedback", return_value=1)
def test_feedback_valid_all_fields(_mock):
    response = client.post("/api/feedback", json={
        "generation_id": 13,
        "rating": 4,
        "tag": "melancholy",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    _mock.assert_called_once_with(
        generation_id=13,
        rating=4,
        tag="melancholy",
    )


@patch("app.main.db.save_feedback", return_value=1)
def test_feedback_optional_fields_omitted(_mock):
    response = client.post("/api/feedback", json={"generation_id": 3})
    assert response.status_code == 200


@patch("app.main.db.save_feedback", return_value=1)
def test_feedback_rating_boundary_valid(_mock):
    for rating in [1, 5]:
        response = client.post("/api/feedback", json={
            "generation_id": 1,
            "rating": rating,
        })
        assert response.status_code == 200, f"Expected 200 for rating={rating}"


def test_feedback_rating_too_low_returns_422():
    response = client.post("/api/feedback", json={"generation_id": 1, "rating": 0})
    assert response.status_code == 422


def test_feedback_rating_too_high_returns_422():
    response = client.post("/api/feedback", json={"generation_id": 1, "rating": 6})
    assert response.status_code == 422


def test_feedback_tag_too_long_returns_422():
    response = client.post("/api/feedback", json={
        "generation_id": 1,
        "tag": "x" * 121,
    })
    assert response.status_code == 422


def test_feedback_missing_generation_id_returns_422():
    response = client.post("/api/feedback", json={"rating": 3})
    assert response.status_code == 422


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
