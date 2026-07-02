"""Unit tests for the audio converter fallback behaviour."""

from __future__ import annotations

from afriklang_vm.integrations.audio.converter import AudioConverter


def test_forwards_original_when_conversion_disabled() -> None:
    converter = AudioConverter(convert=False)
    payload, filename, ctype = converter.normalize(b"rawbytes", "audio/ogg")
    assert payload == b"rawbytes"
    assert filename.endswith(".ogg")
    assert ctype == "audio/ogg"


def test_defaults_content_type_when_missing() -> None:
    converter = AudioConverter(convert=False)
    payload, filename, ctype = converter.normalize(b"x", None)
    assert payload == b"x"
    assert ctype == "application/octet-stream"
    assert filename.endswith(".ogg")
