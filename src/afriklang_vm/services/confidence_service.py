"""Confidence estimation (traffic-light) for transcriptions.

The Afriklang ASR API does not return a confidence score, so we derive a
heuristic proxy from the transcription itself. Degraded audio tends to produce
highly repetitive output (e.g. the same token repeated), so lexical diversity
is a reasonable, deterministic signal of reliability.

This is intentionally transparent and explainable — never presented as a
guarantee of accuracy (see design doc §7 / §13).
"""

from __future__ import annotations

from afriklang_vm.domain.enums import ConfidenceLevel

_HIGH_THRESHOLD = 0.60
_MEDIUM_THRESHOLD = 0.35


class ConfidenceService:
    """Estimate a confidence score + traffic-light level from text."""

    def evaluate(self, text: str) -> tuple[float, ConfidenceLevel]:
        """Return ``(score in [0,1], ConfidenceLevel)``."""
        words = text.split()
        total = len(words)

        if total == 0:
            return 0.0, ConfidenceLevel.LOW

        unique = len({w.lower() for w in words})
        diversity = unique / total

        # Very short outputs can't be judged on diversity alone: cap at MEDIUM.
        if total < 3:
            score = min(diversity, 0.5)
            return score, self._level(score)

        return diversity, self._level(diversity)

    @staticmethod
    def _level(score: float) -> ConfidenceLevel:
        if score >= _HIGH_THRESHOLD:
            return ConfidenceLevel.HIGH
        if score >= _MEDIUM_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        return ConfidenceLevel.LOW
