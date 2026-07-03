"""Vercel serverless entrypoint for the FastAPI app.

Vercel's Python runtime detects the ASGI ``app`` object and serves it.

⚠️ Serverless caveats (see README / ETAT_AVANCEMENT.md):
- Filesystem is read-only except ``/tmp`` (ephemeral) → SQLite data does NOT
  persist between invocations. Fine for ``/docs`` and ``/health``; the WhatsApp
  history/preferences are best-effort only on this platform.
- No ffmpeg → keep ``AUDIO_CONVERT_TO_WAV=false``.
For full, stateful hosting use a container platform (Railway / Fly / Render).
"""

from __future__ import annotations

import os
import sys

# Make the ``src`` layout importable on Vercel.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Writable, ephemeral location for the demo SQLite DB.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/afriklang.db")
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("TWILIO_VALIDATE_SIGNATURE", "false")

from afriklang_vm.main import app  # noqa: E402

__all__ = ["app"]
