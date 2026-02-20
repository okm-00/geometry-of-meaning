import json
import logging
import re
from dataclasses import dataclass

from openai import OpenAI, APIConnectionError, APIStatusError

from app import config

logger = logging.getLogger(__name__)


class LLMConnectionError(RuntimeError):
    """Raised when the LM Studio server cannot be reached at all."""


class LLMResponseError(RuntimeError):
    """Raised when LM Studio returns an HTTP error status."""


class LLMParseError(RuntimeError):
    """Raised when the LLM response cannot be parsed into a valid StoryResult."""


_SYSTEM_PROMPT = """\
You are a creative fiction writer. Your task is to generate a short interactive story.

Respond with ONLY a valid JSON object — no markdown fences, no explanation, no extra text.

The JSON must have exactly this structure:
{
  "body": ["paragraph 1", "paragraph 2", "paragraph 3"],
  "endings": ["ending A", "ending B"]
}

Rules:
- "body" must contain 3 or 4 paragraphs that set up the story. Do not resolve the story here.
- "endings" must contain exactly 2 paragraphs. Each is a distinct final paragraph that resolves
  the story in a different direction. Ending A and ending B must feel meaningfully different —
  not just paraphrases of each other. One can be hopeful, the other bittersweet, for example.
- Each paragraph is a single string of 3–6 sentences.
- Write in third person, past tense.
- All stories must be science fiction and must feature robots as central characters.
- Do not include titles, chapter headings, or any text outside the JSON object.\
"""

_USER_PROMPT = "Generate a short interactive story now. /no_think"


@dataclass
class StoryResult:
    body: list[str]
    endings: list[str]


def generate_story() -> StoryResult:
    """
    Call LM Studio to generate a story with two alternative endings.

    Returns a StoryResult with 3-4 body paragraphs and exactly 2 endings.
    Raises LLMConnectionError, LLMResponseError, or LLMParseError on failure.
    """
    client = OpenAI(
        base_url=config.LM_STUDIO_BASE_URL,
        api_key=config.LM_STUDIO_API_KEY,
        timeout=config.LM_STUDIO_TIMEOUT_SECONDS,
    )

    try:
        response = client.chat.completions.create(
            model=config.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_PROMPT},
            ],
            temperature=0.85,
        )
    except APIConnectionError as e:
        raise LLMConnectionError(
            f"Could not connect to LM Studio at {config.LM_STUDIO_BASE_URL}. "
            f"Ensure LM Studio is running and the local server is enabled. "
            f"Underlying error: {e}"
        ) from e
    except APIStatusError as e:
        raise LLMResponseError(
            f"LM Studio returned HTTP {e.status_code}. "
            f"Check that model '{config.LM_STUDIO_MODEL}' is loaded in LM Studio. "
            f"Underlying error: {e.message}"
        ) from e

    raw = response.choices[0].message.content or ""
    return _parse_response(raw)


def _parse_response(raw: str) -> StoryResult:
    """
    Parse and validate the LLM JSON response into a StoryResult.

    Raises LLMParseError with diagnostic context if the response is malformed.
    """
    raw = raw.strip()
    logger.debug("Raw LLM response: %r", raw[:1000])

    # Strip <think>...</think> reasoning blocks (e.g. Qwen3 without /no_think)
    if "<think>" in raw:
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Strip markdown code fences if the model wrapped the JSON anyway
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            line for line in lines if not line.startswith("```")
        ).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise LLMParseError(
            f"LLM response was not valid JSON. "
            f"Parse error: {e}. "
            f"Raw response (first 500 chars): {raw[:500]!r}"
        ) from e

    body = data.get("body")
    endings = data.get("endings")

    if not isinstance(body, list) or len(body) < 2:
        raise LLMParseError(
            f"LLM response JSON missing or invalid 'body' field. "
            f"Expected a list of 3-4 strings, got: {body!r}"
        )

    if not isinstance(endings, list) or len(endings) != 2:
        raise LLMParseError(
            f"LLM response JSON missing or invalid 'endings' field. "
            f"Expected a list of exactly 2 strings, got: {endings!r}"
        )

    if not all(isinstance(p, str) for p in body):
        raise LLMParseError(
            f"'body' paragraphs must all be strings, got: {body!r}"
        )

    if not all(isinstance(e, str) for e in endings):
        raise LLMParseError(
            f"'endings' must all be strings, got: {endings!r}"
        )

    return StoryResult(body=body, endings=endings)
