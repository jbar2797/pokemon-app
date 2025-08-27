#!/usr/bin/env bash
set -Eeuo pipefail

# Usage:
#   scripts/open_pr.sh <head-branch> [base-branch]
#
# Example:
#   scripts/open_pr.sh feature/s16-api-cards main

HEAD="${1:-$(git rev-parse --abbrev-ref HEAD)}"
BASE="${2:-main}"

REPO="$(git remote get-url origin | sed -E 's#.*github\.com[:/](.+)\.git#\1#')"

echo "Repository: ${REPO}"
echo "Branch: ${HEAD}  Base: ${BASE}"

if [[ "${HEAD}" == "${BASE}" ]]; then
  echo "ERROR: head and base are both '${BASE}'. You cannot open a PR from ${BASE} to ${BASE}." >&2
  echo "Tip: create a feature branch first:" >&2
  echo "  bash scripts/start_feature.sh feature/sXX-something" >&2
  exit 2
fi

# If a PR already exists for this head branch, do nothing.
if gh pr view --repo "${REPO}" --head "${HEAD}" >/dev/null 2>&1; then
  echo "PR already exists for ${HEAD} → ${BASE}."
else
  echo "Creating PR for ${HEAD} → ${BASE}…"
  gh pr create \
    --repo "${REPO}" \
    --base "${BASE}" \
    --head "${HEAD}" \
    --title "$(git log -1 --pretty=%s)" \
    --body  "Automated PR opened by scripts/open_pr.sh"
fi

# Try to enable squash auto-merge (harmless if restricted)
gh pr merge --repo "${REPO}" "${HEAD}" --squash --delete-branch --auto || true

echo "Done."
