#!/usr/bin/env bash
# scripts/commit_and_open_pr.sh
# Usage:
#   bash scripts/commit_and_open_pr.sh "<commit message>" "<PR title>" "<PR body>"
#
# This script:
#   1) Runs pre-commit on staged changes (idempotent)
#   2) Commits any staged changes with the provided message
#   3) Pushes the current branch
#   4) Calls scripts/open_pr.sh to open (or reuse) a PR, and enable squash auto-merge

set -Eeuo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: bash scripts/commit_and_open_pr.sh <commit-msg> <pr-title> <pr-body>" >&2
  exit 2
fi

COMMIT_MSG="$1"
PR_TITLE="$2"
PR_BODY="$3"

# Resolve repo root so we can always call open_pr.sh reliably
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Show branch / remote for context
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
BASE="main"
echo "==> Current branch: ${BRANCH}"

# Run pre-commit on staged changes (idempotent)
echo "==> Stage & commit"
uv run pre-commit run --all-files || true

# Commit if there is anything staged or changed; otherwise allow no-op
if ! git diff --cached --quiet || ! git diff --quiet; then
  git add -A
  git commit -m "${COMMIT_MSG}"
else
  echo "Nothing to commit (working tree clean)."
fi

# Push the current branch
echo "==> Push branch"
git push -u origin "${BRANCH}" || true

# Call our PR helper; if it fails, print a helpful message
echo "==> Open or reuse PR via scripts/open_pr.sh"
if [[ -x "${REPO_ROOT}/scripts/open_pr.sh" ]]; then
  bash "${REPO_ROOT}/scripts/open_pr.sh" "${BRANCH}" "${BASE}" "${PR_TITLE}" "${PR_BODY}" || true
else
  echo "WARNING: scripts/open_pr.sh not found or not executable; install it or run 'gh pr create' manually." >&2
fi

echo "All done: PR should be open (or reused) and CI running."
