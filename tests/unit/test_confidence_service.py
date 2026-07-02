"""Unit tests for the heuristic confidence estimator."""

from __future__ import annotations

import pytest

from afriklang_vm.domain.enums import ConfidenceLevel
from afriklang_vm.services.confidence_service import ConfidenceService


@pytest.fixture
def service() -> ConfidenceService:
    return ConfidenceService()


def test_empty_is_low(service: ConfidenceService) -> None:
    score, level = service.evaluate("")
    assert score == 0.0
    assert level is ConfidenceLevel.LOW


def test_repetitive_output_is_low(service: ConfidenceService) -> None:
    # Degraded-audio style output: one token repeated many times.
    score, level = service.evaluate("ɛyɛ " * 20)
    assert level is ConfidenceLevel.LOW
    assert score < 0.35


def test_diverse_output_is_high(service: ConfidenceService) -> None:
    score, level = service.evaluate("bonjour je voudrais signaler un probleme sur ma ligne mobile")
    assert level is ConfidenceLevel.HIGH
    assert score >= 0.6


def test_short_output_capped_at_medium(service: ConfidenceService) -> None:
    _, level = service.evaluate("bonjour merci")
    assert level in {ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW}
