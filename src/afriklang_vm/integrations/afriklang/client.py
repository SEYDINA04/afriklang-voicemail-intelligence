"""Async client for the Afriklang ASR API."""

from __future__ import annotations

import httpx

from afriklang_vm.domain.enums import Language
from afriklang_vm.integrations.afriklang.models import AsrResponse


class AfriklangError(RuntimeError):
    """Raised when the ASR API returns an error or is unreachable."""


class AfriklangClient:
    """Thin async wrapper over the Afriklang transcription endpoints."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def health(self) -> dict[str, object]:
        """Return the API health payload."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/health")
            resp.raise_for_status()
            data: dict[str, object] = resp.json()
            return data

    async def transcribe(
        self,
        language: Language,
        audio: bytes,
        *,
        filename: str = "voicemail",
        content_type: str = "application/octet-stream",
    ) -> AsrResponse:
        """Transcribe audio bytes in the given language.

        Raises:
            AfriklangError: on network failure or non-2xx response.
        """
        url = f"{self._base_url}/transcribe/{language.value}"
        files = {"file": (filename, audio, content_type)}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(url, files=files)
                resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise AfriklangError(
                f"ASR API returned {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AfriklangError(f"ASR API request failed: {exc}") from exc

        return AsrResponse.model_validate(resp.json())
