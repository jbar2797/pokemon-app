#!/usr/bin/env bash
# scripts/open_pr.sh
# Usage:
#   bash scripts/open_pr.sh <branch> <base> "<PR title>" "<PR body>"

set -Eeuo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: bash scripts/open_pr.sh <branch> <base> \"<PR title>\" \"<PR body>\"" >&2
  exit 2
fi

BRANCH="$1"
BASE="$2"
PR_TITLE="$3"
PR_BODY="$4"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

echo "Repository: $(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo unknown)"
echo "Branch: ${BRANCH}  Base: ${BASE}"

# Create or open PR
if gh pr view "${BRANCH}" >/dev/null 2>&1; then
  echo "PR already exists for ${BRANCH}"
else
  gh pr create \
    --base "${BASE}" \
    --head "${BRANCH}" \
    --title "${PR_TITLE}" \
    --body  "${PR_BODY}"
fi

# Watch latest PR run (if any)
RUN_ID="$(gh run list --branch "${BRANCH}" --event pull_request --limit 1 --json databaseId -q '.[0].databaseId' || true)"
if [[ -n "${RUN_ID:-}" ]]; then
  gh run watch "${RUN_ID}" --interval 5 || true
  echo "Conclusion: $(gh run view "${RUN_ID}" --json conclusion -q '.conclusion' 2>/dev/null || echo unknown)"
else
  echo "No PR run found yet (push usually triggers it)."
fi

# Request squash auto-merge (harmless if restricted)
gh pr merge "${BRANCH}" --squash --delete-branch --auto || true
