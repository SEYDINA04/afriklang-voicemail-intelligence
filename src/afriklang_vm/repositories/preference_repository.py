"""Repository for user preferences (chosen language per WhatsApp number)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from afriklang_vm.domain.enums import Language
from afriklang_vm.domain.models import UserPreference


class PreferenceRepository:
    """Read/write per-user language preferences."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_language(self, whatsapp_id: str) -> Language | None:
        """Return the stored language for a user, or None if unset."""
        result = await self._session.get(UserPreference, whatsapp_id)
        return Language(result.language) if result else None

    async def set_language(self, whatsapp_id: str, language: Language) -> None:
        """Upsert the language preference for a user."""
        existing = await self._session.get(UserPreference, whatsapp_id)
        if existing is None:
            self._session.add(UserPreference(whatsapp_id=whatsapp_id, language=language))
        else:
            existing.language = language

    async def list_all(self) -> list[UserPreference]:
        """Return all preferences (used by seed/reporting)."""
        result = await self._session.execute(select(UserPreference))
        return list(result.scalars().all())
