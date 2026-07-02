"""Unit tests for enums (language command parsing, confidence display)."""

from __future__ import annotations

from afriklang_vm.domain.enums import ConfidenceLevel, Language, Urgency


def test_language_from_command_aliases() -> None:
    assert Language.from_command("/wo") is Language.WOLOF
    assert Language.from_command("wolof") is Language.WOLOF
    assert Language.from_command("/twi") is Language.TWI
    assert Language.from_command("tw") is Language.TWI
    assert Language.from_command("/fr") is None


def test_language_labels() -> None:
    assert Language.WOLOF.label == "Wolof"
    assert Language.TWI.label == "Twi"


def test_confidence_emojis() -> None:
    assert ConfidenceLevel.HIGH.emoji == "🟢"
    assert ConfidenceLevel.MEDIUM.emoji == "🟠"
    assert ConfidenceLevel.LOW.emoji == "🔴"


def test_urgency_emoji() -> None:
    assert Urgency.URGENT.emoji == "🔴"
    assert Urgency.NORMAL.emoji == "⚪"
