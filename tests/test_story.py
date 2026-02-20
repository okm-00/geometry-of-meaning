"""
Unit tests for app/story.py.

No network calls — the OpenAI client is mocked throughout.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.story import (
    StoryResult,
    LLMConnectionError,
    LLMResponseError,
    LLMParseError,
    _parse_response,
    generate_story,
)
from openai import APIConnectionError, APIStatusError


# ---------------------------------------------------------------------------
# _parse_response — pure parsing, no network
# ---------------------------------------------------------------------------

VALID_STORY = {
    "body": ["Para one.", "Para two.", "Para three."],
    "endings": ["Ending A.", "Ending B."],
}


def test_parse_valid_json():
    raw = json.dumps(VALID_STORY)
    result = _parse_response(raw)
    assert isinstance(result, StoryResult)
    assert result.body == VALID_STORY["body"]
    assert result.endings == VALID_STORY["endings"]


def test_parse_strips_think_block():
    raw = "<think>\nAll this reasoning...\n</think>\n" + json.dumps(VALID_STORY)
    result = _parse_response(raw)
    assert result.body == VALID_STORY["body"]


def test_parse_strips_markdown_fences():
    raw = "```json\n" + json.dumps(VALID_STORY) + "\n```"
    result = _parse_response(raw)
    assert result.body == VALID_STORY["body"]


def test_parse_invalid_json_raises():
    with pytest.raises(LLMParseError, match="not valid JSON"):
        _parse_response("this is not json")


def test_parse_empty_string_raises():
    with pytest.raises(LLMParseError):
        _parse_response("")


def test_parse_missing_body_raises():
    raw = json.dumps({"endings": ["A", "B"]})
    with pytest.raises(LLMParseError, match="body"):
        _parse_response(raw)


def test_parse_missing_endings_raises():
    raw = json.dumps({"body": ["p1", "p2", "p3"]})
    with pytest.raises(LLMParseError, match="endings"):
        _parse_response(raw)


def test_parse_body_too_short_raises():
    raw = json.dumps({"body": ["only one"], "endings": ["A", "B"]})
    with pytest.raises(LLMParseError, match="body"):
        _parse_response(raw)


def test_parse_endings_wrong_count_raises():
    raw = json.dumps({"body": ["p1", "p2", "p3"], "endings": ["only one"]})
    with pytest.raises(LLMParseError, match="endings"):
        _parse_response(raw)


def test_parse_non_string_body_paragraph_raises():
    raw = json.dumps({"body": ["p1", 42, "p3"], "endings": ["A", "B"]})
    with pytest.raises(LLMParseError, match="body"):
        _parse_response(raw)


def test_parse_non_string_ending_raises():
    raw = json.dumps({"body": ["p1", "p2", "p3"], "endings": ["A", None]})
    with pytest.raises(LLMParseError, match="endings"):
        _parse_response(raw)


# ---------------------------------------------------------------------------
# generate_story — mocked OpenAI client
# ---------------------------------------------------------------------------

def _make_mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("app.story.OpenAI")
def test_generate_story_success(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response(
        json.dumps(VALID_STORY)
    )

    result = generate_story()
    assert isinstance(result, StoryResult)
    assert len(result.endings) == 2


@patch("app.story.OpenAI")
def test_generate_story_connection_error(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = APIConnectionError(
        request=MagicMock()
    )

    with pytest.raises(LLMConnectionError, match="LM Studio"):
        generate_story()


@patch("app.story.OpenAI")
def test_generate_story_api_status_error(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_client.chat.completions.create.side_effect = APIStatusError(
        message="model not found",
        response=mock_response,
        body=None,
    )

    with pytest.raises(LLMResponseError, match="404"):
        generate_story()


@patch("app.story.OpenAI")
def test_generate_story_malformed_response_raises_parse_error(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response(
        "not json at all"
    )

    with pytest.raises(LLMParseError):
        generate_story()
