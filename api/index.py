"""Vercel serverless entrypoint for the FastAPI app.

Vercel's Python runtime detects the ASGI ``app`` object and serves it.

⚠️ Serverless caveats (see README / ETAT_AVANCEMENT.md):
- Filesystem is read-only except ``/tmp`` (ephemeral) → SQLite data persists
  only within a warm instance, not across cold starts. Fine for a demo; use a
  container platform (Railway / Fly / Render) for durable persistence.
- No ffmpeg → keep ``AUDIO_CONVERT_TO_WAV=false``.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Make the ``src`` layout importable on Vercel.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Writable, ephemeral location for the demo SQLite DB + serverless-safe pooling.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:////tmp/afriklang.db")
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("TWILIO_VALIDATE_SIGNATURE", "false")
os.environ.setdefault("DB_NULLPOOL", "1")

from fastapi import Request  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402

from afriklang_vm.config import get_settings  # noqa: E402
from afriklang_vm.db.engine import init_db, init_engine  # noqa: E402
from afriklang_vm.main import app, build_container  # noqa: E402

_init_lock = asyncio.Lock()
_initialized = False


async def _ensure_startup(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Run engine/DB/container init on the request's own event loop (once).

    Vercel does not reliably invoke ASGI lifespan events, so we lazily
    initialize on the first request instead of at process startup.
    """
    global _initialized
    if not _initialized:
        async with _init_lock:
            if not _initialized:
                settings = get_settings()
                init_engine(settings.database_url)
                await init_db()
                if not getattr(app.state, "container", None):
                    app.state.container = build_container(settings)
                _initialized = True
    return await call_next(request)


app.add_middleware(BaseHTTPMiddleware, dispatch=_ensure_startup)

__all__ = ["app"]
