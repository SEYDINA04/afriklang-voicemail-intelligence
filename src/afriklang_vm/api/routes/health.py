"""Health-check endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from afriklang_vm.api.deps import AppContainer, get_container

router = APIRouter(tags=["health"])


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Landing page: redirect to the interactive API docs."""
    return RedirectResponse(url="/docs")


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe for the bot service itself."""
    return {"status": "ok", "service": "afriklang-voicemail"}


@router.get("/health/asr")
async def asr_health(container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    """Readiness probe that also checks the upstream Afriklang ASR API."""
    try:
        upstream = await container.afriklang.health()
        return {"status": "ok", "asr": upstream}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"status": "degraded", "error": str(exc)}
