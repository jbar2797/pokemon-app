#!/usr/bin/env bash
# scripts/start_feature.sh
# Purpose: Create a new feature branch from latest main and verify env.
# Usage: bash scripts/start_feature.sh <new-branch-name>

set -Eeuo pipefail

REPO="${REPO:-$HOME/projects/pokemon-app}"
BRANCH="${1:-}"

if [[ -z "$BRANCH" ]]; then
  echo "Usage: bash scripts/start_feature.sh <new-branch-name>" >&2
  exit 2
fi

main() {
  cd "$REPO"
  echo "==> Create/reset feature branch from latest main: $BRANCH"
  git fetch origin main
  git checkout -B "$BRANCH" origin/main

  echo "==> Sync environment"
  uv lock && uv sync --dev

  echo "==> Gates on the new branch (quick check)"
  uv run ruff check .
  uv run mypy .
  uv run pytest -q || true

  echo "==> Feature branch ready: $BRANCH"
}

main "$@"
