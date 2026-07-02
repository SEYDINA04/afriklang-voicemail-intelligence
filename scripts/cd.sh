#!/usr/bin/env bash
# Local CD — mirrors .github/workflows/cd.yml (build & push image to GHCR).
# Usage:
#   ./scripts/cd.sh                 # build + push (needs GHCR auth)
#   ./scripts/cd.sh --build-only    # build image locally, no push
#
# Auth for push (needs a token with `write:packages`):
#   export GHCR_TOKEN=<pat>         # or CR_PAT; falls back to `gh auth token`
set -euo pipefail

cd "$(dirname "$0")/.."

REGISTRY="ghcr.io"
OWNER="$(gh api user --jq .login 2>/dev/null | tr '[:upper:]' '[:lower:]')"
IMAGE_NAME="${REGISTRY}/${OWNER}/afriklang-voicemail-intelligence"
SHA="$(git rev-parse --short HEAD)"
BUILD_ONLY="${1:-}"

echo "▶ Building image ${IMAGE_NAME} (tags: latest, main, sha-${SHA})…"
docker build \
  -t "${IMAGE_NAME}:latest" \
  -t "${IMAGE_NAME}:main" \
  -t "${IMAGE_NAME}:sha-${SHA}" \
  .

if [ "${BUILD_ONLY}" = "--build-only" ]; then
  echo "✅ Build done (push skipped: --build-only)."
  exit 0
fi

TOKEN="${GHCR_TOKEN:-${CR_PAT:-$(gh auth token)}}"

echo "▶ Logging in to ${REGISTRY} as ${OWNER}…"
echo "${TOKEN}" | docker login "${REGISTRY}" -u "${OWNER}" --password-stdin

echo "▶ Pushing tags…"
docker push "${IMAGE_NAME}:latest"
docker push "${IMAGE_NAME}:main"
docker push "${IMAGE_NAME}:sha-${SHA}"

echo "✅ CD local: image pushed to ${IMAGE_NAME}"
