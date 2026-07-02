"""Repository for voice messages, transcriptions, tags, and full-text search."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from afriklang_vm.domain.enums import ConfidenceLevel, Language, Urgency
from afriklang_vm.domain.models import MessageTag, VoiceMessage


class MessageRepository:
    """Persist and query transcribed voice messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        whatsapp_id: str,
        language: Language,
        transcribed_text: str,
        confidence_score: float | None,
        confidence_level: ConfidenceLevel,
        urgency: Urgency,
        tags: list[str],
        media_content_type: str | None = None,
        audio_url: str | None = None,
    ) -> VoiceMessage:
        """Insert a voice message with its tags."""
        message = VoiceMessage(
            whatsapp_id=whatsapp_id,
            language=language,
            transcribed_text=transcribed_text,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            urgency=urgency,
            media_content_type=media_content_type,
            audio_url=audio_url,
            tags=[MessageTag(tag=t) for t in tags],
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def search(self, whatsapp_id: str, query: str, *, limit: int = 10) -> list[VoiceMessage]:
        """Full-text search over a user's transcriptions (FTS5).

        Falls back to a LIKE query if the FTS query cannot be parsed.
        """
        fts_query = _to_fts_query(query)
        try:
            stmt = text(
                """
                SELECT vm.id
                FROM voice_messages_fts fts
                JOIN voice_messages vm ON vm.id = fts.rowid
                WHERE voice_messages_fts MATCH :q
                  AND vm.whatsapp_id = :wid
                ORDER BY vm.created_at DESC
                LIMIT :lim
                """
            )
            rows = await self._session.execute(
                stmt, {"q": fts_query, "wid": whatsapp_id, "lim": limit}
            )
            ids = [row[0] for row in rows.fetchall()]
        except Exception:
            return await self._search_like(whatsapp_id, query, limit=limit)

        if not ids:
            return []
        result = await self._session.execute(select(VoiceMessage).where(VoiceMessage.id.in_(ids)))
        by_id = {m.id: m for m in result.scalars().all()}
        return [by_id[i] for i in ids if i in by_id]

    async def _search_like(self, whatsapp_id: str, query: str, *, limit: int) -> list[VoiceMessage]:
        stmt = (
            select(VoiceMessage)
            .where(
                VoiceMessage.whatsapp_id == whatsapp_id,
                VoiceMessage.transcribed_text.ilike(f"%{query}%"),
            )
            .order_by(VoiceMessage.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def recent(self, whatsapp_id: str, *, limit: int = 5) -> list[VoiceMessage]:
        """Return a user's most recent messages."""
        stmt = (
            select(VoiceMessage)
            .where(VoiceMessage.whatsapp_id == whatsapp_id)
            .order_by(VoiceMessage.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


def _to_fts_query(query: str) -> str:
    """Turn free text into a safe FTS5 MATCH expression (prefix, AND-joined)."""
    tokens = [t for t in "".join(c if c.isalnum() else " " for c in query).split() if t]
    if not tokens:
        return '""'
    return " AND ".join(f"{t}*" for t in tokens)
