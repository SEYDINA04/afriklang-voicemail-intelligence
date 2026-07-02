.PHONY: help install dev run test lint fmt typecheck check seed docker-build ci-local cd-local clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Sync dependencies (incl. dev + audio extra)
	uv sync --all-extras

dev:  ## Run the API with autoreload
	uv run uvicorn afriklang_vm.main:app --reload --host 0.0.0.0 --port 8000

run:  ## Run the API (production-ish)
	uv run uvicorn afriklang_vm.main:app --host 0.0.0.0 --port 8000

test:  ## Run tests with coverage
	uv run pytest --cov --cov-report=term-missing

lint:  ## Lint (ruff)
	uv run ruff check .

fmt:  ## Format (ruff)
	uv run ruff format .

typecheck:  ## Static typing (mypy)
	uv run mypy src

check: lint typecheck test  ## Run all quality gates

seed:  ## Seed demo data
	uv run python scripts/seed_demo.py

ci-local:  ## Run the full CI pipeline locally (mirrors ci.yml)
	./scripts/ci.sh

cd-local:  ## Build & push the image to GHCR locally (mirrors cd.yml)
	./scripts/cd.sh

docker-build:  ## Build the Docker image
	docker build -t afriklang-voicemail:local .

clean:  ## Remove caches and build artifacts
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage coverage.xml dist build
