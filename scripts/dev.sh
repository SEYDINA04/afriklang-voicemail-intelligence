#!/usr/bin/env bash
set -euo pipefail
exec uv run uvicorn afriklang_vm.main:app --reload --host 0.0.0.0 --port 8000
