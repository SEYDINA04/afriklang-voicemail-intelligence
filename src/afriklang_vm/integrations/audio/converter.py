"""Convert inbound WhatsApp audio (OGG/Opus) to WAV 16 kHz mono.

The Afriklang ASR API is Whisper-based and decodes audio server-side, so
conversion is optional. When ``convert`` is disabled or ffmpeg/pydub are
unavailable, the original bytes are forwarded unchanged.
"""

from __future__ import annotations

import io
import shutil

import structlog

logger = structlog.get_logger(__name__)


class AudioConverter:
    """Best-effort audio normalization to WAV 16 kHz mono."""

    def __init__(self, *, convert: bool = False) -> None:
        self._convert = convert and self._ffmpeg_available()
        if convert and not self._convert:
            logger.warning("audio.ffmpeg_missing", note="forwarding original audio bytes")

    @staticmethod
    def _ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    def normalize(self, audio: bytes, content_type: str | None) -> tuple[bytes, str, str]:
        """Return ``(bytes, filename, content_type)`` ready for the ASR API."""
        if not self._convert:
            ext = _extension_for(content_type)
            return audio, f"voicemail{ext}", content_type or "application/octet-stream"

        try:
            from pydub import AudioSegment  # noqa: PLC0415 (optional dependency)

            source_format = _pydub_format(content_type)
            segment = AudioSegment.from_file(io.BytesIO(audio), format=source_format)
            segment = segment.set_frame_rate(16000).set_channels(1)
            out = io.BytesIO()
            segment.export(out, format="wav")
            return out.getvalue(), "voicemail.wav", "audio/wav"
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("audio.convert_failed", error=str(exc))
            ext = _extension_for(content_type)
            return audio, f"voicemail{ext}", content_type or "application/octet-stream"


def _extension_for(content_type: str | None) -> str:
    mapping = {
        "audio/ogg": ".ogg",
        "audio/ogg; codecs=opus": ".ogg",
        "audio/opus": ".opus",
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/amr": ".amr",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
    }
    if content_type:
        return mapping.get(content_type.split(";")[0].strip(), ".ogg")
    return ".ogg"


def _pydub_format(content_type: str | None) -> str:
    if not content_type:
        return "ogg"
    base = content_type.split(";")[0].strip()
    return {
        "audio/ogg": "ogg",
        "audio/opus": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp4": "m4a",
        "audio/amr": "amr",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
    }.get(base, "ogg")
