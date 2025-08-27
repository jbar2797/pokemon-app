#!/usr/bin/env bash
set -Eeuo pipefail

# Usage: bash scripts/open_pr.sh <branch> <base> <title> <body>

BRANCH="${1:?Usage: $0 <branch> <base> <title> <body>}"
BASE="${2:?Usage: $0 <branch> <base> <title> <body>}"
TITLE="${3:?Usage: $0 <branch> <base> <title> <body>}"
BODY="${4:?Usage: $0 <branch> <base> <title> <body>}"

if gh pr view "$BRANCH" >/dev/null 2>&1; then
  echo "PR already exists for $BRANCH"
else
  gh pr create \
    --base "$BASE" \
    --head "$BRANCH" \
    --title "$TITLE" \
    --body  "$BODY"
fi

# Optional, harmless if auto-merge is restricted
gh pr merge "$BRANCH" --squash --delete-branch --auto || true
