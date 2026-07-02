"""Bot orchestration: route inbound WhatsApp messages to replies."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from afriklang_vm.domain.enums import Language
from afriklang_vm.domain.schemas import InboundMessage, MessageView, TranscriptionResult
from afriklang_vm.repositories.message_repository import MessageRepository
from afriklang_vm.repositories.preference_repository import PreferenceRepository
from afriklang_vm.services.search_service import SearchService
from afriklang_vm.services.transcription_service import TranscriptionService

_HELP = (
    "🎙️ *Afriklang Voicemail Intelligence*\n\n"
    "Enregistre un message vocal (Twi ou Wolof) directement dans ce chat "
    "et reçois sa transcription en quelques secondes.\n\n"
    "*Commandes :*\n"
    "• /twi — transcrire en Twi (par défaut)\n"
    "• /wo — transcrire en Wolof\n"
    "• /lang — voir ta langue actuelle\n"
    "• /search <mot> — chercher dans tes messages\n"
    "• /help — afficher cette aide"
)


class BotService:
    """Route text commands and voice notes to formatted WhatsApp replies."""

    def __init__(
        self,
        transcription_service: TranscriptionService,
        search_service: SearchService,
        default_language: Language,
    ) -> None:
        self._transcription = transcription_service
        self._search = search_service
        self._default_language = default_language

    # ── Text commands ───────────────────────────────────────
    async def handle_text(self, session: AsyncSession, inbound: InboundMessage) -> str:
        body = inbound.body.strip()
        lowered = body.lower()

        if lowered in {"/help", "help", "start", "/start", "hi", "hello"}:
            return _HELP

        if lowered in {"/lang", "lang"}:
            lang = await self._current_language(session, inbound.whatsapp_id)
            return f"🌍 Langue actuelle : *{lang.label}* ({lang.value})."

        language = Language.from_command(body)
        if language is not None and body.startswith("/"):
            prefs = PreferenceRepository(session)
            await prefs.set_language(inbound.whatsapp_id, language)
            return (
                f"✅ Langue réglée sur *{language.label}*.\n"
                "🎙️ Enregistre maintenant un message vocal, je le transcris."
            )

        if lowered.startswith("/search"):
            query = body[len("/search") :].strip()
            if not query:
                return "🔎 Utilisation : /search <mot-clé>"
            results = await self._search.search(session, inbound.whatsapp_id, query)
            return _format_search(query, results)

        return (
            "🤖 Je transcris les *messages vocaux* en Twi et Wolof.\n"
            "🎙️ Enregistre un vocal, ou tape /help pour l'aide."
        )

    # ── Voice notes ─────────────────────────────────────────
    async def handle_media(
        self,
        session: AsyncSession,
        inbound: InboundMessage,
        audio: bytes,
        content_type: str | None,
    ) -> str:
        language = await self._current_language(session, inbound.whatsapp_id)
        repo = MessageRepository(session)
        result = await self._transcription.process(
            repo=repo,
            whatsapp_id=inbound.whatsapp_id,
            language=language,
            audio=audio,
            content_type=content_type,
            audio_url=inbound.media_url,
        )
        return _format_transcription(result)

    async def _current_language(self, session: AsyncSession, whatsapp_id: str) -> Language:
        prefs = PreferenceRepository(session)
        stored = await prefs.get_language(whatsapp_id)
        return stored or self._default_language


# ── Reply formatting ────────────────────────────────────────
def _format_transcription(result: TranscriptionResult) -> str:
    text = result.text or "_(aucune parole détectée)_"
    lines = [
        f"📝 *Transcription* ({result.language.label})",
        "",
        text,
        "",
        f"{result.confidence_level.emoji} {result.confidence_level.label}",
    ]
    if result.urgency.value == "urgent":
        lines.append("🚨 *Message prioritaire*")
    if result.tags:
        lines.append("🏷️ " + ", ".join(result.tags))
    return "\n".join(lines)


def _format_search(query: str, results: list[MessageView]) -> str:
    if not results:
        return f'🔎 Aucun résultat pour "{query}".'
    lines = [f'🔎 *Résultats pour "{query}"* ({len(results)}) :', ""]
    for i, m in enumerate(results, start=1):
        snippet = m.transcribed_text[:120] + ("…" if len(m.transcribed_text) > 120 else "")
        date = m.created_at.strftime("%d/%m %H:%M")
        lines.append(f"{i}. {m.confidence_level.emoji} [{date}] {snippet}")
    return "\n".join(lines)
