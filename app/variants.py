"""
Variant registry: every generation variant is defined here.

A variant is the complete specification for one experimental condition —
LLM prompts (what the model writes) plus harness configuration (what
structure the harness builds around the output).

Adding a new variant = one new entry in VARIANTS.
"""

from dataclasses import dataclass

from app.features import EndingStrategy


@dataclass(frozen=True)
class VariantConfig:
    name: str
    system_prompt: str
    user_prompt: str
    body_paragraphs: int = 1
    ending_strategy: EndingStrategy = EndingStrategy.HARNESS


_USER_PROMPT = "Write your Sebald-style meditation on Coke Zero now. /no_think"

_BASELINE_SYSTEM = """\
You are W.G. Sebald. Write in your distinctive prose style: long, winding sentences \
that drift between memoir, history, and melancholy observation; digressions that feel \
inevitable rather than accidental; a narrator who is both present and dissolving into \
the material. Your subject is Coke Zero — encountered perhaps on a train, in a museum \
café, in a petrol station on a grey afternoon. Let the object open outward into time, \
loss, and the strangeness of modern existence. Write a single paragraph of 4–6 sentences.\
"""

_HARNESS_SYSTEM = """\
You are W.G. Sebald. Write in your distinctive prose style: long, accumulative sentences \
threaded through with footnote-like digressions; a tone of muted, almost anthropological \
curiosity; an eye for the overlooked and the obsolescent. Your subject is Coke Zero — \
but approach it through a specific, concrete detail: the can's graphic design, the \
particular sound it makes when opened in a quiet room, the date printed on its underside. \
Let that detail become a portal into the industrial history of sweetness, the manufacture \
of desire, and the erasure of the body from its own pleasures. Write a single paragraph \
of 4–6 sentences.\
"""


VARIANTS: dict[str, VariantConfig] = {
    "baseline": VariantConfig(
        name="baseline",
        system_prompt=_BASELINE_SYSTEM,
        user_prompt=_USER_PROMPT,
        body_paragraphs=1,
        ending_strategy=EndingStrategy.NONE,
    ),
    "harness": VariantConfig(
        name="harness",
        system_prompt=_HARNESS_SYSTEM,
        user_prompt=_USER_PROMPT,
        body_paragraphs=1,
        ending_strategy=EndingStrategy.HARNESS,
    ),
}
