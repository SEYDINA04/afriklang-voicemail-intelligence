"""Persistence models (SQLAlchemy 2.0 declarative)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from afriklang_vm.domain.enums import ConfidenceLevel, Language, Urgency


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class UserPreference(Base):
    """Per-user (WhatsApp number) settings — notably the chosen language."""

    __tablename__ = "user_preferences"

    whatsapp_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language: Mapped[Language] = mapped_column(String(8))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class VoiceMessage(Base):
    """An inbound voice note and its transcription result."""

    __tablename__ = "voice_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    whatsapp_id: Mapped[str] = mapped_column(String(64), index=True)
    language: Mapped[Language] = mapped_column(String(8))
    media_content_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    transcribed_text: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        String(8), default=ConfidenceLevel.MEDIUM
    )
    urgency: Mapped[Urgency] = mapped_column(String(8), default=Urgency.NORMAL)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    tags: Mapped[list[MessageTag]] = relationship(
        back_populates="message", cascade="all, delete-orphan", lazy="selectin"
    )


class MessageTag(Base):
    """A category/keyword tag attached to a voice message."""

    __tablename__ = "message_tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("voice_messages.id", ondelete="CASCADE"), index=True
    )
    tag: Mapped[str] = mapped_column(String(64))

    message: Mapped[VoiceMessage] = relationship(back_populates="tags")
