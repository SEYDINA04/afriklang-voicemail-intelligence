"""Application configuration (12-factor, typed via pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from afriklang_vm.domain.enums import Language


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Twilio ──────────────────────────────────────────────
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")
    twilio_whatsapp_from: str = Field(default="whatsapp:+14155238886")
    twilio_validate_signature: bool = Field(default=True)

    # ── Afriklang ASR ───────────────────────────────────────
    afriklang_base_url: str = Field(default="https://asr.afriklang.com")
    afriklang_timeout_seconds: float = Field(default=60.0)
    default_language: Language = Field(default=Language.TWI)

    # ── Application ─────────────────────────────────────────
    app_env: Literal["local", "test", "staging", "production"] = Field(default="local")
    log_level: str = Field(default="INFO")
    database_url: str = Field(default="sqlite+aiosqlite:///./data/afriklang.db")

    # ── Audio ───────────────────────────────────────────────
    audio_convert_to_wav: bool = Field(default=False)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
