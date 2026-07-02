"""Unit tests for keyword tagging and urgency detection."""

from __future__ import annotations

import pytest

from afriklang_vm.domain.enums import Urgency
from afriklang_vm.services.keyword_service import KeywordService


@pytest.fixture
def service() -> KeywordService:
    return KeywordService()


def test_detects_money_category(service: KeywordService) -> None:
    tags, urgency = service.tag("Mon transfert mobile money est bloqué")
    assert "money" in tags
    assert "complaint" in tags
    assert urgency is Urgency.URGENT  # complaint implies urgency


def test_urgent_keyword_sets_urgency(service: KeywordService) -> None:
    tags, urgency = service.tag("C'est urgent, rappelez-moi vite")
    assert "urgent" in tags
    assert urgency is Urgency.URGENT


def test_accent_insensitive_matching(service: KeywordService) -> None:
    # "reseau" without accent should still match the "network" category.
    tags, _ = service.tag("probleme de reseau")
    assert "network" in tags


def test_no_keywords_is_normal(service: KeywordService) -> None:
    tags, urgency = service.tag("bonjour comment allez vous")
    assert tags == []
    assert urgency is Urgency.NORMAL


def test_empty_text(service: KeywordService) -> None:
    tags, urgency = service.tag("")
    assert tags == []
    assert urgency is Urgency.NORMAL
