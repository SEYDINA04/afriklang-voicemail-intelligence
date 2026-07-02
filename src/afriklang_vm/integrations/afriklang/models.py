"""Response models for the Afriklang ASR API.

Observed response shape (v2.0.0)::

    {"text": "...", "language": "twi", "model": "afriklang_asr_tw1"}

Note: the API does **not** return a confidence score, so confidence is
derived heuristically downstream (see ConfidenceService).
"""

from __future__ import annotations

from pydantic import BaseModel


class AsrResponse(BaseModel):
    """Parsed Afriklang transcription response."""

    text: str = ""
    language: str | None = None
    model: str | None = None
