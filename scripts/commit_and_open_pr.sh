#!/usr/bin/env bash
# scripts/commit_and_open_pr.sh
# Purpose: Commit all changes, push branch, create PR, watch CI, request auto-merge.
# Usage: bash scripts/commit_and_open_pr.sh "<commit-msg>" "<pr-title>" "<pr-body>"
# Requires: scripts/open_pr (if present, will be used), otherwise falls back to gh.

set -Eeuo pipefail

REPO="${REPO:-$HOME/projects/pokemon-app}"
BASE="${BASE:-main}"
BRANCH="$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"

if [[ $# -lt 3 ]]; then
  echo "Usage: bash scripts/commit_and_open_pr.sh <commit-msg> <pr-title> <pr-body>" >&2
  exit 2
fi

COMMIT_MSG="$1"
PR_TITLE="$2"
PR_BODY="$3"

main() {
  cd "$REPO"

  if [[ -z "$BRANCH" || "$BRANCH" == "HEAD" ]]; then
    echo "ERROR: Could not determine current branch. Are you inside a git branch?" >&2
    exit 1
  fi

  echo "==> Stage & commit"
  git add -A
  git commit -m "$COMMIT_MSG" || true

  echo "==> Push branch"
  git push -u origin "$BRANCH" || true

  # Prefer your open_pr wrapper if present
  if command -v open_pr >/dev/null 2>&1; then
    echo "==> Using local 'open_pr' helper"
    open_pr "$BRANCH" "$BASE" "$PR_TITLE" "$PR_BODY" || true
  else
    echo "==> 'open_pr' not found; using gh fallback"
    if gh pr view "$BRANCH" >/dev/null 2>&1; then
      echo "PR already exists for ${BRANCH}"
    else
      gh pr create \
        --base "$BASE" \
        --head "$BRANCH" \
        --title "$PR_TITLE" \
        --body  "$PR_BODY"
    fi
  fi

  echo "==> Watch latest PR CI run (if present)"
  RUN_ID="$(gh run list --branch "$BRANCH" --event pull_request --limit 1 --json databaseId -q '.[0].databaseId' || true)"
  if [[ -n "${RUN_ID:-}" ]]; then
    gh run watch "$RUN_ID" --interval 5 || true
    echo "Conclusion: $(gh run view "$RUN_ID" --json conclusion -q '.conclusion' 2>/dev/null || echo unknown)"
  else
    echo "No PR run found yet (push usually triggers it)."
  fi

  echo "==> Request squash auto-merge (harmless if restricted)"
  gh pr merge "$BRANCH" --squash --delete-branch --auto || true

  echo "All done: PR should be open and CI running."
}

main "$@"
