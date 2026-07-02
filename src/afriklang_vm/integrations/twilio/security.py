"""Twilio webhook signature validation."""

from __future__ import annotations

from twilio.request_validator import RequestValidator


class TwilioSignatureValidator:
    """Validate the ``X-Twilio-Signature`` header on inbound webhooks."""

    def __init__(self, auth_token: str, *, enabled: bool = True) -> None:
        self._validator = RequestValidator(auth_token)
        self._enabled = enabled

    def is_valid(self, url: str, params: dict[str, str], signature: str | None) -> bool:
        """Return True if the request signature is valid (or validation disabled)."""
        if not self._enabled:
            return True
        if not signature:
            return False
        return bool(self._validator.validate(url, params, signature))
