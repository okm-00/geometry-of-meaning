import logging
import re
import time
from dataclasses import dataclass

from openai import OpenAI, APIConnectionError, APIStatusError

from app import config
from app.features import EndingStrategy
from app.variants import VariantConfig

logger = logging.getLogger(__name__)

TEMPERATURE = 0.85

# Prompts used for harness-generated endings.
# Both variants share the same ending style; promote to VariantConfig if they diverge.
_ENDING_SYSTEM = """\
You are W.G. Sebald. Write a single closing paragraph in your distinctive prose style: \
melancholy, digressive, precise. The paragraph should feel like a natural conclusion — \
or an opening onto something unresolved.\
"""


class LLMConnectionError(RuntimeError):
    """Raised when the LM Studio server cannot be reached at all."""


class LLMResponseError(RuntimeError):
    """Raised when LM Studio returns an HTTP error status."""


@dataclass
class StoryResult:
    body: list[str]
    endings: list[str]   # empty list when ending_strategy is NONE
    condition: str
    system_prompt: str
    user_prompt: str
    timing_ms: int


def generate_story(variant: VariantConfig) -> StoryResult:
    """
    Generate a story for the given variant.

    Makes one LLM call for the body. If variant.ending_strategy is HARNESS,
    makes two additional calls to produce alternate endings A and B.

    Raises LLMConnectionError or LLMResponseError on failure.
    """
    client = OpenAI(
        base_url=config.LM_STUDIO_BASE_URL,
        api_key=config.LM_STUDIO_API_KEY,
        timeout=config.LM_STUDIO_TIMEOUT_SECONDS,
    )

    start = time.monotonic()

    body_text = _call_llm(client, variant.system_prompt, variant.user_prompt).strip()

    endings: list[str] = []
    if variant.ending_strategy == EndingStrategy.HARNESS:
        ending_user = (
            f"The story so far:\n\n{body_text}\n\n"
            "Write a single closing paragraph. /no_think"
        )
        ending_a = _call_llm(client, _ENDING_SYSTEM, ending_user).strip()
        ending_b = _call_llm(client, _ENDING_SYSTEM, ending_user).strip()
        endings = [ending_a, ending_b]

    return StoryResult(
        body=[body_text],
        endings=endings,
        condition=variant.name,
        system_prompt=variant.system_prompt,
        user_prompt=variant.user_prompt,
        timing_ms=int((time.monotonic() - start) * 1000),
    )


def _call_llm(client: OpenAI, system_prompt: str, user_prompt: str) -> str:
    """Make a single chat completion call; return raw content string."""
    try:
        response = client.chat.completions.create(
            model=config.LM_STUDIO_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
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
    # Strip <think>...</think> reasoning blocks produced by Qwen3 thinking mode.
    if "<think>" in raw:
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    return raw
