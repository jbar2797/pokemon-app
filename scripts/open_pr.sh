#!/usr/bin/env bash
set -Eeuo pipefail

BRANCH="${1:-}"
BASE="${2:-main}"

usage() {
  echo "Usage: scripts/open_pr.sh <branch> [base=main]" >&2
  exit 2
}

[[ -n "$BRANCH" ]] || usage

REPO_DIR="$(git rev-parse --show-toplevel)"
cd "$REPO_DIR"

# Ensure branch exists and is pushed
git fetch origin "$BASE"
git checkout -B "$BRANCH" "origin/$BASE" >/dev/null 2>&1 || git checkout "$BRANCH"
git push -u origin "$BRANCH" >/dev/null 2>&1 || true

# Bail out early if there are no changes vs base
if git diff --quiet "origin/$BASE...$BRANCH"; then
  echo "No commits between $BASE and $BRANCH. Nothing to PR." >&2
  exit 0
fi

# Create PR if it does not exist
if gh pr view "$BRANCH" >/dev/null 2>&1; then
  echo "PR already exists for $BRANCH"
else
  TITLE="$(git log -1 --pretty=%s || echo "Change set")"
  BODY="Automated PR via scripts/open_pr.sh"
  gh pr create --base "$BASE" --head "$BRANCH" --title "$TITLE" --body "$BODY"
fi

# Watch latest run (if any) then request auto-merge (harmless if restricted)
RUN_ID="$(gh run list --branch "$BRANCH" --event pull_request --limit 1 --json databaseId -q '.[0].databaseId' || true)"
if [[ -n "${RUN_ID:-}" ]]; then
  echo "Watching CI run ${RUN_ID}…"
  gh run watch "$RUN_ID" --interval 5 || true
  echo "Conclusion: $(gh run view "$RUN_ID" --json conclusion -q .conclusion 2>/dev/null || echo unknown)"
fi

gh pr merge "$BRANCH" --squash --delete-branch --auto || true
echo "PR flow complete."
