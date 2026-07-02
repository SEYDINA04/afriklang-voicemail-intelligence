"""FastAPI application factory and entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from afriklang_vm import __version__
from afriklang_vm.api.deps import AppContainer
from afriklang_vm.api.router import api_router
from afriklang_vm.config import Settings, get_settings
from afriklang_vm.db.engine import dispose_engine, init_db, init_engine
from afriklang_vm.integrations.afriklang.client import AfriklangClient
from afriklang_vm.integrations.audio.converter import AudioConverter
from afriklang_vm.integrations.twilio.client import TwilioClient
from afriklang_vm.integrations.twilio.security import TwilioSignatureValidator
from afriklang_vm.logging_config import configure_logging
from afriklang_vm.services.command_service import BotService
from afriklang_vm.services.confidence_service import ConfidenceService
from afriklang_vm.services.keyword_service import KeywordService
from afriklang_vm.services.search_service import SearchService
from afriklang_vm.services.transcription_service import TranscriptionService

logger = structlog.get_logger(__name__)


def build_container(settings: Settings) -> AppContainer:
    """Wire application singletons from settings."""
    afriklang = AfriklangClient(
        settings.afriklang_base_url, timeout=settings.afriklang_timeout_seconds
    )
    converter = AudioConverter(convert=settings.audio_convert_to_wav)
    transcription = TranscriptionService(
        asr_client=afriklang,
        converter=converter,
        keyword_service=KeywordService(),
        confidence_service=ConfidenceService(),
    )
    bot = BotService(
        transcription_service=transcription,
        search_service=SearchService(),
        default_language=settings.default_language,
    )
    twilio = TwilioClient(
        settings.twilio_account_sid,
        settings.twilio_auth_token,
        settings.twilio_whatsapp_from,
    )
    signature = TwilioSignatureValidator(
        settings.twilio_auth_token, enabled=settings.twilio_validate_signature
    )
    return AppContainer(
        settings=settings,
        afriklang=afriklang,
        twilio=twilio,
        signature=signature,
        bot=bot,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, json_logs=settings.app_env != "local")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_engine(settings.database_url)
        await init_db()
        app.state.container = build_container(settings)
        logger.info("app.startup", env=settings.app_env, version=__version__)
        yield
        await dispose_engine()
        logger.info("app.shutdown")

    app = FastAPI(
        title="Afriklang Voicemail Intelligence",
        description="WhatsApp bot transcribing Twi/Wolof voice notes via Afriklang ASR.",
        version=__version__,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()
