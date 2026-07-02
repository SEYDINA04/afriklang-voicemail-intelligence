"""Twilio client: download inbound media and send WhatsApp replies."""

from __future__ import annotations

import httpx


class TwilioMediaError(RuntimeError):
    """Raised when media cannot be downloaded from Twilio."""


class TwilioClient:
    """Minimal async Twilio helper for media download + outbound messages."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        whatsapp_from: str,
        *,
        timeout: float = 30.0,
    ) -> None:
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from = whatsapp_from
        self._timeout = timeout

    async def download_media(self, media_url: str) -> tuple[bytes, str]:
        """Download media bytes from a Twilio ``MediaUrl``.

        Returns:
            (content, content_type)
        """
        auth = (self._account_sid, self._auth_token)
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                resp = await client.get(media_url, auth=auth)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TwilioMediaError(f"Failed to download media: {exc}") from exc

        content_type = resp.headers.get("content-type", "application/octet-stream")
        return resp.content, content_type

    async def send_message(self, to: str, body: str) -> None:
        """Send a WhatsApp text message via the Twilio REST API."""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}/Messages.json"
        data = {"From": self._from, "To": to, "Body": body}
        auth = (self._account_sid, self._auth_token)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, data=data, auth=auth)
            resp.raise_for_status()
