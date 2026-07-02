"""Seed demo transcriptions so the pitch has searchable data.

Inserts a handful of realistic Twi/Wolof/French voice-message transcriptions
for a demo user, running them through the same tagging + confidence services
used in production (no ASR call needed).

Usage:
    uv run python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio

from afriklang_vm.config import get_settings
from afriklang_vm.db.engine import dispose_engine, init_db, init_engine, session_scope
from afriklang_vm.domain.enums import Language
from afriklang_vm.repositories.message_repository import MessageRepository
from afriklang_vm.repositories.preference_repository import PreferenceRepository
from afriklang_vm.services.confidence_service import ConfidenceService
from afriklang_vm.services.keyword_service import KeywordService

DEMO_USER = "whatsapp:+221770000000"

DEMO_MESSAGES: list[tuple[Language, str]] = [
    (Language.WOLOF, "Sama xaalis bloqué na ci mobile money, urgent la, dama war koo gaaw"),
    (Language.TWI, "Me sika a mede kɔɔ momo no ankɔ, ɛyɛ urgent, mesrɛ mo boa me ntɛm"),
    (Language.WOLOF, "Reseau bi baaxul ci sama gox, signal amul dara"),
    (Language.TWI, "Me network no nyɛ adwuma, internet no nkɔ"),
    (Language.WOLOF, "Bëgg naa recharge sama SIM waaye activation bi antuwul"),
    (Language.TWI, "Medaase, me nsɛm no baa yie, akwaaba"),
]


async def main() -> None:
    settings = get_settings()
    init_engine(settings.database_url)
    await init_db()

    keywords = KeywordService()
    confidence = ConfidenceService()

    async with session_scope() as session:
        await PreferenceRepository(session).set_language(DEMO_USER, Language.WOLOF)
        repo = MessageRepository(session)
        for language, text in DEMO_MESSAGES:
            tags, urgency = keywords.tag(text)
            score, level = confidence.evaluate(text)
            await repo.create(
                whatsapp_id=DEMO_USER,
                language=language,
                transcribed_text=text,
                confidence_score=score,
                confidence_level=level,
                urgency=urgency,
                tags=tags,
            )
            print(f"[{language.value}] {level.emoji} {urgency.value:7} {tags} :: {text[:50]}…")

    await dispose_engine()
    print(f"\nSeeded {len(DEMO_MESSAGES)} messages for {DEMO_USER}.")


if __name__ == "__main__":
    asyncio.run(main())
