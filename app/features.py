"""
EndingStrategy — the vocabulary for how a variant generates alternate endings.

This module defines only the enum. The choice of strategy for a given variant
lives on VariantConfig.ending_strategy, not here.
"""

from enum import Enum


class EndingStrategy(Enum):
    NONE    = "none"    # body only; no endings generated
    HARNESS = "harness" # two separate LLM calls produce ending A and ending B
    # future: KDE = "kde"  # KDE-scored candidates
