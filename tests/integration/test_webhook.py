"""Integration tests for the Twilio WhatsApp webhook (external APIs mocked)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
import respx

from afriklang_vm.config import Settings
from afriklang_vm.main import create_app

MEDIA_URL = "https://api.twilio.com/media/sample.ogg"


@pytest_asyncio.fixture
async def client(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=transport, base_url="http://test") as c,
    ):
        yield c


async def test_health(client: httpx.AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_help_command(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/whatsapp/webhook",
        data={"From": "whatsapp:+221770000001", "Body": "/help", "NumMedia": "0"},
    )
    assert resp.status_code == 200
    assert "Afriklang Voicemail Intelligence" in resp.text


async def test_set_language(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/whatsapp/webhook",
        data={"From": "whatsapp:+221770000002", "Body": "/wo", "NumMedia": "0"},
    )
    assert resp.status_code == 200
    assert "Wolof" in resp.text


@respx.mock
async def test_voice_note_transcription_and_search(client: httpx.AsyncClient) -> None:
    user = "whatsapp:+221770000003"

    # Mock Twilio media download.
    respx.get(MEDIA_URL).mock(
        return_value=httpx.Response(
            200, content=b"FAKEAUDIO", headers={"content-type": "audio/ogg"}
        )
    )
    # Mock Afriklang ASR (default language = twi).
    respx.post("https://asr.test/transcribe/twi").mock(
        return_value=httpx.Response(
            200,
            json={
                "text": "urgent mon transfert money est bloque",
                "language": "twi",
                "model": "afriklang_asr_tw1",
            },
        )
    )

    # Inbound voice note.
    resp = await client.post(
        "/whatsapp/webhook",
        data={
            "From": user,
            "Body": "",
            "NumMedia": "1",
            "MediaUrl0": MEDIA_URL,
            "MediaContentType0": "audio/ogg",
        },
    )
    assert resp.status_code == 200
    assert "Transcription" in resp.text
    assert "prioritaire" in resp.text.lower()  # urgent tag detected

    # It should now be searchable.
    search = await client.post(
        "/whatsapp/webhook",
        data={"From": user, "Body": "/search transfert", "NumMedia": "0"},
    )
    assert search.status_code == 200
    assert "transfert" in search.text.lower()


async def test_invalid_signature_rejected(settings: Settings) -> None:
    # Re-enable signature validation to assert rejection.
    strict = settings.model_copy(update={"twilio_validate_signature": True})
    app = create_app(strict)
    transport = httpx.ASGITransport(app=app)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=transport, base_url="http://test") as c,
    ):
        resp = await c.post(
            "/whatsapp/webhook",
            data={"From": "whatsapp:+221770000004", "Body": "/help"},
        )
    assert resp.status_code == 403
