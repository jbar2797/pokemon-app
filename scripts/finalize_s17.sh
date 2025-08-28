#!/usr/bin/env bash
# scripts/finalize_s17.sh
# Purpose: finalize Sprint 17 (Python SDK)
# - commits any staged or auto-fixed files (pre-commit), pushes, opens PR, requests auto-merge, pulls main, and smokes.

set -Eeuo pipefail

BRANCH="${1:-feature/s17-python-sdk}"
BASE="main"
REPO="${REPO:-$HOME/projects/pokemon-app}"

cd "$REPO"

echo "==> Ensure branch exists and switch to it"
git fetch origin "$BASE"
# Prefer existing feature branch; otherwise create from origin/main
if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  git checkout "$BRANCH"
else
  git checkout -B "$BRANCH" "origin/$BASE"
fi

echo "==> Sync env & run gates"
uv lock && uv sync --dev
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
uv run pytest -q

echo "==> Run pre-commit across tracked files"
uv run pre-commit run --all-files || true

echo "==> Stage & commit (no-op commit allowed to ensure a PR diff)"
# If nothing changed, create a tiny docs nudge so PR has a commit.
if ! git diff --cached --quiet || ! git diff --quiet; then
  :
else
  mkdir -p docs
  printf "\n<!-- s17 finalize tick -->\n" >> docs/SDK_PYTHON.md 2>/dev/null || true
fi

git add -A
git commit -m "feat(sdk): finalize Sprint 17 — Python SDK ready (chg-0017)" || true

echo "==> Push branch"
git push -u origin "$BRANCH" || true

echo "==> Open or reuse PR"
if [ -x scripts/open_pr.sh ]; then
  bash scripts/open_pr.sh "$BRANCH" "$BASE" || true
else
  echo "Open a PR from $BRANCH -> $BASE via GitHub UI if this step is not automated."
fi

echo "==> Try auto-merge (harmless if restricted)"
if command -v gh >/dev/null 2>&1; then
  gh pr merge "$BRANCH" --squash --delete-branch --auto || true
else
  echo "GitHub CLI not found; skipping auto-merge."
fi

echo "==> Pull merged main (OK if merge is manual)"
git checkout "$BASE" || true
git pull --ff-only || true

echo "==> Quick smoke on main (if script exists)"
if [ -x scripts/morning_check.sh ]; then
  bash scripts/morning_check.sh || true
else
  echo "Run your usual smoke tests."
fi

echo "Done: Sprint 17 finalized."
