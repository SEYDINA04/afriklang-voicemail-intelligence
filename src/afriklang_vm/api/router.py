"""Aggregate all API routers."""

from __future__ import annotations

from fastapi import APIRouter

from afriklang_vm.api.routes import health, whatsapp

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(whatsapp.router)
