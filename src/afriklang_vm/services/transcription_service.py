"""Transcription pipeline: audio -> ASR -> tags -> confidence -> persistence."""

from __future__ import annotations

import structlog

from afriklang_vm.domain.enums import Language
from afriklang_vm.domain.schemas import TranscriptionResult
from afriklang_vm.integrations.afriklang.client import AfriklangClient
from afriklang_vm.integrations.audio.converter import AudioConverter
from afriklang_vm.repositories.message_repository import MessageRepository
from afriklang_vm.services.confidence_service import ConfidenceService
from afriklang_vm.services.keyword_service import KeywordService

logger = structlog.get_logger(__name__)


class TranscriptionService:
    """Orchestrate the full voicemail transcription flow."""

    def __init__(
        self,
        asr_client: AfriklangClient,
        converter: AudioConverter,
        keyword_service: KeywordService,
        confidence_service: ConfidenceService,
    ) -> None:
        self._asr = asr_client
        self._converter = converter
        self._keywords = keyword_service
        self._confidence = confidence_service

    async def process(
        self,
        *,
        repo: MessageRepository,
        whatsapp_id: str,
        language: Language,
        audio: bytes,
        content_type: str | None,
        audio_url: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe, tag, score, persist, and return the enriched result."""
        payload, filename, ctype = self._converter.normalize(audio, content_type)

        asr = await self._asr.transcribe(language, payload, filename=filename, content_type=ctype)
        text = asr.text.strip()

        tags, urgency = self._keywords.tag(text)
        score, level = self._confidence.evaluate(text)

        await repo.create(
            whatsapp_id=whatsapp_id,
            language=language,
            transcribed_text=text,
            confidence_score=score,
            confidence_level=level,
            urgency=urgency,
            tags=tags,
            media_content_type=content_type,
            audio_url=audio_url,
        )

        logger.info(
            "transcription.done",
            whatsapp_id=whatsapp_id,
            language=language.value,
            urgency=urgency.value,
            confidence=level.value,
            tags=tags,
            chars=len(text),
        )

        return TranscriptionResult(
            text=text,
            language=language,
            confidence_score=score,
            confidence_level=level,
            urgency=urgency,
            tags=tags,
        )
