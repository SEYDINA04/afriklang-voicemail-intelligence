"""Domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class Language(StrEnum):
    """Languages supported by the Afriklang ASR API."""

    WOLOF = "wo"
    TWI = "twi"

    @property
    def label(self) -> str:
        """Human-readable label."""
        return {Language.WOLOF: "Wolof", Language.TWI: "Twi"}[self]

    @classmethod
    def from_command(cls, token: str) -> Language | None:
        """Map a chat command token (e.g. '/wo', 'twi') to a Language."""
        normalized = token.strip().lstrip("/").lower()
        aliases = {
            "wo": cls.WOLOF,
            "wolof": cls.WOLOF,
            "twi": cls.TWI,
            "tw": cls.TWI,
        }
        return aliases.get(normalized)


class ConfidenceLevel(StrEnum):
    """Traffic-light confidence buckets shown to the agent."""

    HIGH = "high"  # 🟢 reliable
    MEDIUM = "medium"  # 🟠 verify with audio
    LOW = "low"  # 🔴 manual review

    @property
    def emoji(self) -> str:
        return {
            ConfidenceLevel.HIGH: "🟢",
            ConfidenceLevel.MEDIUM: "🟠",
            ConfidenceLevel.LOW: "🔴",
        }[self]

    @property
    def label(self) -> str:
        return {
            ConfidenceLevel.HIGH: "confiance élevée",
            ConfidenceLevel.MEDIUM: "confiance moyenne — vérifier l'audio",
            ConfidenceLevel.LOW: "confiance faible — écoute manuelle recommandée",
        }[self]


class Urgency(StrEnum):
    """Urgency level derived from keyword detection."""

    URGENT = "urgent"
    NORMAL = "normal"

    @property
    def emoji(self) -> str:
        return "🔴" if self is Urgency.URGENT else "⚪"
