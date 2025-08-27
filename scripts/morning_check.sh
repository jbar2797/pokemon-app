#!/usr/bin/env bash
# scripts/morning_check.sh
# Purpose: Morning sanity on `main` + run the API smoke test.
# Usage: bash scripts/morning_check.sh

set -Eeuo pipefail

REPO="${REPO:-$HOME/projects/pokemon-app}"

main() {
  echo "==> Morning check starting"
  cd "$REPO"

  echo "==> Ensure we're on main and up-to-date"
  git fetch origin main
  git checkout main
  git pull --ff-only

  echo "==> Sync env and run gates"
  uv lock && uv sync --dev
  uv run ruff check .
  uv run mypy .
  uv run pytest -q

  echo "==> Run API smoke (bash version)"
  if [[ -x scripts/smoke_api.sh ]]; then
    bash scripts/smoke_api.sh
  else
    echo "ERROR: scripts/smoke_api.sh not found or not executable" >&2
    exit 1
  fi

  echo "==> Morning check complete: main is healthy."
}

main "$@"
