#!/usr/bin/env bash
# Local CI — mirrors .github/workflows/ci.yml (quality gates).
# Usage: ./scripts/ci.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "▶ Sync dependencies (frozen, all extras)…"
uv sync --all-extras --frozen

echo "▶ Lint (ruff check)…"
uv run ruff check .

echo "▶ Format check (ruff format --check)…"
uv run ruff format --check .

echo "▶ Type check (mypy)…"
uv run mypy src

echo "▶ Tests (pytest + coverage)…"
uv run pytest --cov --cov-report=xml --cov-report=term-missing

echo "✅ CI local: all quality gates passed."
