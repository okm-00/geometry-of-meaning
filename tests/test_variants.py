"""
Tests for app/variants.py.

Verifies that the VARIANTS registry is correctly shaped and that baseline and
harness are genuinely distinct configurations.
"""

from app.features import EndingStrategy
from app.variants import VARIANTS, VariantConfig


def test_variants_has_baseline_and_harness():
    assert "baseline" in VARIANTS
    assert "harness" in VARIANTS


def test_all_variants_are_variant_config_instances():
    for name, vc in VARIANTS.items():
        assert isinstance(vc, VariantConfig), f"{name!r} is not a VariantConfig"


def test_variant_name_matches_registry_key():
    for key, vc in VARIANTS.items():
        assert vc.name == key, f"VariantConfig.name {vc.name!r} != registry key {key!r}"


def test_each_variant_has_non_empty_system_prompt():
    for name, vc in VARIANTS.items():
        assert vc.system_prompt.strip(), f"{name!r} has empty system_prompt"


def test_each_variant_has_non_empty_user_prompt():
    for name, vc in VARIANTS.items():
        assert vc.user_prompt.strip(), f"{name!r} has empty user_prompt"


def test_each_variant_body_paragraphs_at_least_one():
    for name, vc in VARIANTS.items():
        assert vc.body_paragraphs >= 1, f"{name!r} body_paragraphs < 1"


def test_baseline_and_harness_have_different_system_prompts():
    assert VARIANTS["baseline"].system_prompt != VARIANTS["harness"].system_prompt


def test_each_variant_has_ending_strategy():
    for name, vc in VARIANTS.items():
        assert isinstance(vc.ending_strategy, EndingStrategy), (
            f"{name!r} ending_strategy is not an EndingStrategy"
        )


def test_no_variant_system_prompt_contains_json_instructions():
    for name, vc in VARIANTS.items():
        assert "JSON" not in vc.system_prompt, (
            f"{name!r} system_prompt still contains JSON instructions"
        )


def test_baseline_uses_none_ending_strategy():
    assert VARIANTS["baseline"].ending_strategy == EndingStrategy.NONE


def test_harness_uses_harness_ending_strategy():
    assert VARIANTS["harness"].ending_strategy == EndingStrategy.HARNESS
