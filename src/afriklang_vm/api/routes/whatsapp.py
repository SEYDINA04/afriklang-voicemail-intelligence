"""Twilio WhatsApp webhook: receive voice notes / commands, reply with TwiML."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request, Response
from twilio.twiml.messaging_response import MessagingResponse

from afriklang_vm.api.deps import (
    get_bot,
    get_signature_validator,
    get_twilio,
)
from afriklang_vm.db.engine import session_scope
from afriklang_vm.domain.schemas import InboundMessage
from afriklang_vm.integrations.twilio.client import TwilioClient
from afriklang_vm.integrations.twilio.security import TwilioSignatureValidator
from afriklang_vm.services.command_service import BotService

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["whatsapp"])


def _public_url(request: Request) -> str:
    """Reconstruct the public URL Twilio used to sign the request."""
    proto = request.headers.get("x-forwarded-proto")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if proto and host:
        return f"{proto}://{host}{request.url.path}"
    return str(request.url)


def _twiml(message: str) -> Response:
    resp = MessagingResponse()
    resp.message(message)
    return Response(content=str(resp), media_type="application/xml")


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request,
    bot: BotService = Depends(get_bot),
    twilio: TwilioClient = Depends(get_twilio),
    validator: TwilioSignatureValidator = Depends(get_signature_validator),
) -> Response:
    """Handle an inbound WhatsApp message from the Twilio Sandbox."""
    form = await request.form()
    params = {k: str(v) for k, v in form.items()}
    signature = request.headers.get("X-Twilio-Signature")

    if not validator.is_valid(_public_url(request), params, signature):
        logger.warning("webhook.invalid_signature", from_=params.get("From"))
        return Response(status_code=403, content="Invalid signature")

    inbound = InboundMessage(
        whatsapp_id=params.get("From", ""),
        body=params.get("Body", ""),
        num_media=int(params.get("NumMedia", "0") or 0),
        media_url=params.get("MediaUrl0"),
        media_content_type=params.get("MediaContentType0"),
    )

    logger.info(
        "webhook.received",
        from_=inbound.whatsapp_id,
        num_media=inbound.num_media,
        has_body=bool(inbound.body),
    )

    try:
        async with session_scope() as session:
            if inbound.has_media and inbound.media_url:
                audio, content_type = await twilio.download_media(inbound.media_url)
                reply = await bot.handle_media(session, inbound, audio, content_type)
            else:
                reply = await bot.handle_text(session, inbound)
    except Exception as exc:  # noqa: BLE001 - always answer the user gracefully
        logger.exception("webhook.error", error=str(exc))
        reply = (
            "⚠️ Désolé, une erreur est survenue lors du traitement de ton message. "
            "Réessaie dans un instant."
        )

    return _twiml(reply)
