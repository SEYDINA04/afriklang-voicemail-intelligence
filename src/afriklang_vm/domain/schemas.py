"""Data-transfer objects (Pydantic) used across service boundaries."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from afriklang_vm.domain.enums import ConfidenceLevel, Language, Urgency


class InboundMessage(BaseModel):
    """Normalized representation of a Twilio WhatsApp webhook payload."""

    whatsapp_id: str
    body: str = ""
    num_media: int = 0
    media_url: str | None = None
    media_content_type: str | None = None

    @property
    def has_media(self) -> bool:
        return self.num_media > 0 and self.media_url is not None


class TranscriptionResult(BaseModel):
    """Outcome of an ASR call, enriched with confidence + tags."""

    text: str
    language: Language
    confidence_score: float | None = None
    confidence_level: ConfidenceLevel
    urgency: Urgency
    tags: list[str] = []


class MessageView(BaseModel):
    """Read model for a stored voice message (search results, history)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    language: Language
    transcribed_text: str
    confidence_level: ConfidenceLevel
    urgency: Urgency
    created_at: datetime
