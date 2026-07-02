"""Full-text search over a user's transcription history."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from afriklang_vm.domain.schemas import MessageView
from afriklang_vm.repositories.message_repository import MessageRepository


class SearchService:
    """Query stored transcriptions for a given user."""

    async def search(
        self, session: AsyncSession, whatsapp_id: str, query: str, *, limit: int = 10
    ) -> list[MessageView]:
        repo = MessageRepository(session)
        messages = await repo.search(whatsapp_id, query, limit=limit)
        return [MessageView.model_validate(m) for m in messages]
