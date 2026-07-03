# ── Builder ────────────────────────────────────────────────
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first (better layer caching).
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --extra audio

# Install the project itself.
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra audio

# ── Runtime ────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# ffmpeg enables optional OGG/Opus -> WAV conversion.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DATABASE_URL=sqlite+aiosqlite:///./data/afriklang.db

RUN mkdir -p /app/data && chown app:app /app/data
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request,sys; port=os.getenv('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{port}/health').status==200 else 1)"

# Respect the platform-provided $PORT (Render, Railway, Fly…), default 8000.
CMD ["sh", "-c", "uvicorn afriklang_vm.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
