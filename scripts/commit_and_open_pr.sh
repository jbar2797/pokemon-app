#!/usr/bin/env bash
set -Eeuo pipefail

# Usage:
#   scripts/commit_and_open_pr.sh "<commit-msg>" "<pr-title>" "<pr-body>" [base-branch]
#
# Notes:
# - This script REFUSES to run on 'main' to prevent accidental main commits.
# - It runs pre-commit hooks, commits, pushes, and opens a PR via scripts/open_pr.sh.

if [[ $# -lt 3 ]]; then
  echo "Usage: bash scripts/commit_and_open_pr.sh <commit-msg> <pr-title> <pr-body> [base-branch]" >&2
  exit 2
fi

COMMIT_MSG="$1"
PR_TITLE="$2"
PR_BODY="$3"
BASE="${4:-main}"

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${BRANCH}" == "main" ]]; then
  echo "ERROR: You are on 'main'. We do not commit directly to main." >&2
  echo "Create a feature branch first, then re-run:" >&2
  echo "  bash scripts/start_feature.sh feature/sXX-your-task" >&2
  exit 2
fi

echo "==> Current branch: ${BRANCH}"

echo "==> Stage & commit"
uv run pre-commit run --all-files || true
git add -A
# If nothing is staged, don't fail loudly
git commit -m "${COMMIT_MSG}" || true

echo "==> Push branch"
git push -u origin "${BRANCH}" || git push

echo "==> Open or reuse PR via scripts/open_pr.sh"
bash scripts/open_pr.sh "${BRANCH}" "${BASE}"

echo "All done: PR should be open (or reused) and CI running."
