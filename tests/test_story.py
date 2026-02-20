"""
Unit tests for app/story.py.

No network calls — the OpenAI client is mocked throughout.
"""

from unittest.mock import MagicMock, patch, call

import pytest

from app.story import (
    StoryResult,
    LLMConnectionError,
    LLMResponseError,
    generate_story,
)
from app.features import EndingStrategy
from app.variants import VARIANTS, VariantConfig
from openai import APIConnectionError, APIStatusError


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

# Minimal variant with no endings — used for connection/status error tests.
_VARIANT_NONE = VariantConfig(
    name="test_none",
    system_prompt="test system prompt",
    user_prompt="test user prompt",
    body_paragraphs=1,
    ending_strategy=EndingStrategy.NONE,
)

# Minimal variant with harness endings.
_VARIANT_HARNESS = VariantConfig(
    name="test_harness",
    system_prompt="test system prompt",
    user_prompt="test user prompt",
    body_paragraphs=1,
    ending_strategy=EndingStrategy.HARNESS,
)


def _make_mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# EndingStrategy.NONE — one LLM call, no endings
# ---------------------------------------------------------------------------

@patch("app.story.OpenAI")
def test_generate_story_none_strategy_makes_one_call(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response("Body text.")

    result = generate_story(_VARIANT_NONE)

    assert mock_client.chat.completions.create.call_count == 1
    assert result.endings == []


@patch("app.story.OpenAI")
def test_generate_story_none_strategy_returns_body(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response("  Body text.  ")

    result = generate_story(_VARIANT_NONE)

    assert result.body == ["Body text."]  # stripped


@patch("app.story.OpenAI")
def test_generate_story_none_strategy_sets_condition(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response("Body.")

    result = generate_story(_VARIANT_NONE)

    assert result.condition == "test_none"
    assert result.system_prompt == _VARIANT_NONE.system_prompt
    assert result.user_prompt == _VARIANT_NONE.user_prompt
    assert result.timing_ms >= 0


# ---------------------------------------------------------------------------
# EndingStrategy.HARNESS — three LLM calls, two endings
# ---------------------------------------------------------------------------

@patch("app.story.OpenAI")
def test_generate_story_harness_strategy_makes_three_calls(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _make_mock_response("Body text."),
        _make_mock_response("Ending A."),
        _make_mock_response("Ending B."),
    ]

    result = generate_story(_VARIANT_HARNESS)

    assert mock_client.chat.completions.create.call_count == 3
    assert len(result.endings) == 2


@patch("app.story.OpenAI")
def test_generate_story_harness_strategy_endings_content(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _make_mock_response("Body text."),
        _make_mock_response("  Ending A.  "),
        _make_mock_response("  Ending B.  "),
    ]

    result = generate_story(_VARIANT_HARNESS)

    assert result.endings[0] == "Ending A."   # stripped
    assert result.endings[1] == "Ending B."


@patch("app.story.OpenAI")
def test_generate_story_harness_strategy_body_in_ending_prompt(mock_openai_cls):
    """The ending calls must include the body text as context."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _make_mock_response("The body paragraph."),
        _make_mock_response("Ending A."),
        _make_mock_response("Ending B."),
    ]

    generate_story(_VARIANT_HARNESS)

    # Calls 2 and 3 (index 1 and 2) should contain the body text in the user message.
    for i in (1, 2):
        user_msg = mock_client.chat.completions.create.call_args_list[i][1]["messages"][1]["content"]
        assert "The body paragraph." in user_msg


# ---------------------------------------------------------------------------
# Real VARIANTS — condition names and system prompt distinctness
# ---------------------------------------------------------------------------

@patch("app.story.OpenAI")
def test_baseline_variant_condition_name(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response("Body.")

    result = generate_story(VARIANTS["baseline"])
    assert result.condition == "baseline"


@patch("app.story.OpenAI")
def test_harness_variant_condition_name(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = [
        _make_mock_response("Body."),
        _make_mock_response("Ending A."),
        _make_mock_response("Ending B."),
    ]

    result = generate_story(VARIANTS["harness"])
    assert result.condition == "harness"


@patch("app.story.OpenAI")
def test_baseline_and_harness_use_different_system_prompts(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response("Body.")

    b = generate_story(VARIANTS["baseline"])
    assert b.system_prompt == VARIANTS["baseline"].system_prompt
    assert b.system_prompt != VARIANTS["harness"].system_prompt


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

@patch("app.story.OpenAI")
def test_generate_story_connection_error(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.side_effect = APIConnectionError(
        request=MagicMock()
    )
    with pytest.raises(LLMConnectionError, match="LM Studio"):
        generate_story(_VARIANT_NONE)


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
        generate_story(_VARIANT_NONE)


@patch("app.story.OpenAI")
def test_generate_story_plain_prose_does_not_raise(mock_openai_cls):
    """LLM returning plain prose (no JSON) must no longer cause an error."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.chat.completions.create.return_value = _make_mock_response(
        "The can, set down on the plastic tray-table of a late InterCity service..."
    )
    result = generate_story(_VARIANT_NONE)
    assert len(result.body) == 1
    assert "InterCity" in result.body[0]
