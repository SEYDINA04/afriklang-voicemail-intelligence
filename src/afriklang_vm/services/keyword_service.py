"""Keyword-based tagging and urgency detection.

Deterministic (no AI) per the design document's reliability principle:
AI is used only for transcription; routing/tagging is rule-based so it cannot
"hallucinate" in front of the jury.

Keyword lists cover Twi, Wolof, French and English to match the multilingual
inbound flow described for persona *Kofi*.
"""

from __future__ import annotations

import unicodedata

from afriklang_vm.domain.enums import Urgency

# Category -> keywords (lowercase, accent-insensitive matching applied).
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "urgent": [
        # fr / en
        "urgent",
        "urgence",
        "immediatement",
        "emergency",
        "vite",
        "rapidement",
        # twi
        "ntɛm",
        "prɛko",
        "seesei",
        # wolof
        "gaaw",
        "leegi",
        "bu jamono",
    ],
    "network": [
        "reseau",
        "network",
        "signal",
        "connexion",
        "internet",
        "data",
        "coverage",
        "couverture",
    ],
    "money": [
        "argent",
        "money",
        "mobile money",
        "momo",
        "wari",
        "transfert",
        "transfer",
        "solde",
        "balance",
        "paiement",
        "payment",
        "xaalis",
        "sika",
    ],
    "complaint": [
        "probleme",
        "problem",
        "plainte",
        "complaint",
        "erreur",
        "error",
        "bloque",
        "blocked",
        "marche pas",
        "ne fonctionne",
    ],
    "sim": ["sim", "carte sim", "puce", "activation", "activer", "recharge"],
}

# Categories that also imply urgency.
_URGENT_CATEGORIES = {"urgent", "complaint"}


def _normalize(text: str) -> str:
    """Lowercase and strip accents for robust matching."""
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFD", lowered)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


class KeywordService:
    """Detect category tags and urgency from transcribed text."""

    def __init__(self, category_keywords: dict[str, list[str]] | None = None) -> None:
        self._categories = category_keywords or CATEGORY_KEYWORDS
        # Pre-normalize keywords once.
        self._normalized: dict[str, list[str]] = {
            cat: [_normalize(k) for k in kws] for cat, kws in self._categories.items()
        }

    def tag(self, text: str) -> tuple[list[str], Urgency]:
        """Return ``(tags, urgency)`` for a transcription."""
        haystack = _normalize(text)
        tags = [
            category
            for category, keywords in self._normalized.items()
            if any(kw and kw in haystack for kw in keywords)
        ]
        urgency = (
            Urgency.URGENT if any(tag in _URGENT_CATEGORIES for tag in tags) else Urgency.NORMAL
        )
        return tags, urgency
