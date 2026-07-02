"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from afriklang_vm.config import Settings
from afriklang_vm.db.engine import dispose_engine, init_db, init_engine


@pytest.fixture
def settings(tmp_path) -> Settings:
    """Isolated settings pointing at a temp SQLite DB and a fake ASR host."""
    db_path = tmp_path / "test.db"
    return Settings(
        twilio_account_sid="ACtest",
        twilio_auth_token="testtoken",
        twilio_whatsapp_from="whatsapp:+14155238886",
        twilio_validate_signature=False,
        afriklang_base_url="https://asr.test",
        default_language="twi",
        app_env="test",
        database_url=f"sqlite+aiosqlite:///{db_path}",
        audio_convert_to_wav=False,
    )


@pytest_asyncio.fixture
async def initialized_db(settings: Settings) -> AsyncIterator[None]:
    """Initialize (and dispose) the global async engine for a test."""
    init_engine(settings.database_url)
    await init_db()
    yield
    await dispose_engine()
