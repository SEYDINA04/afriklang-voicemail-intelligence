"""Dependency container and FastAPI dependency accessors."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request

from afriklang_vm.config import Settings
from afriklang_vm.integrations.afriklang.client import AfriklangClient
from afriklang_vm.integrations.twilio.client import TwilioClient
from afriklang_vm.integrations.twilio.security import TwilioSignatureValidator
from afriklang_vm.services.command_service import BotService


@dataclass(slots=True)
class AppContainer:
    """Holds application-wide singletons, built once at startup."""

    settings: Settings
    afriklang: AfriklangClient
    twilio: TwilioClient
    signature: TwilioSignatureValidator
    bot: BotService


def get_container(request: Request) -> AppContainer:
    """Return the app container from application state."""
    container: AppContainer = request.app.state.container
    return container


def get_bot(request: Request) -> BotService:
    return get_container(request).bot


def get_twilio(request: Request) -> TwilioClient:
    return get_container(request).twilio


def get_signature_validator(request: Request) -> TwilioSignatureValidator:
    return get_container(request).signature


def get_settings_dep(request: Request) -> Settings:
    return get_container(request).settings
