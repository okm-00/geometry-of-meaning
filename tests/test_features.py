"""
Tests for app/features.py.
"""

from app.features import EndingStrategy
from app.variants import VARIANTS


def test_ending_strategy_has_none_value():
    assert EndingStrategy.NONE.value == "none"


def test_ending_strategy_has_harness_value():
    assert EndingStrategy.HARNESS.value == "harness"


def test_ending_strategy_values_are_distinct():
    assert EndingStrategy.NONE != EndingStrategy.HARNESS


def test_baseline_variant_uses_none_strategy():
    assert VARIANTS["baseline"].ending_strategy == EndingStrategy.NONE


def test_harness_variant_uses_harness_strategy():
    assert VARIANTS["harness"].ending_strategy == EndingStrategy.HARNESS
