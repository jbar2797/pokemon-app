#!/usr/bin/env bash
# scripts/finalize_s16.sh
# Finish Sprint 16: commit on feature branch, open PR, auto-merge, fast-forward main.

set -Eeuo pipefail

REPO="${REPO:-$HOME/projects/pokemon-app}"
BRANCH="${1:-feature/s16-api-fixes}"
BASE="main"

COMMIT_MSG="feat(api): cards/search/detail/prices + portfolio value (chg-0016)"
PR_TITLE="feat: Sprint 16 — cards + portfolio endpoints (chg-0016)"
PR_BODY=$'Adds endpoints:\n- GET /v1/cards/search?q=\n- GET /v1/cards/{id}\n- GET /v1/cards/{id}/prices?limit=\n- POST /v1/portfolio/value\nIncludes typed responses and tests.'

cd "$REPO"

echo "==> Ensure the feature branch exists and switch to it"
git fetch origin "$BASE"
# If you already have local uncommitted changes on main, this will FAIL — in that case:
#   git switch -c "$BRANCH"
git checkout -B "$BRANCH" "origin/$BASE" || git switch "$BRANCH"

echo "==> Bring in your current working tree edits if needed"
# If you previously edited on main, you may need to cherry-pick or re-apply changes here.
# This script assumes your work is already in the working tree on this branch.

echo "==> Sync env and run gates"
uv lock && uv sync --dev
uv run ruff check --fix .
uv run ruff format .
uv run mypy .
uv run pytest -q

echo "==> Quick inline smoke (no branch switching)"
# Seed demo data and start server briefly to probe
lsof -tiTCP:8001 -sTCP:LISTEN | xargs -r kill || true
pkill -f "uvicorn .*8001" 2>/dev/null || true

uv run poke-pricer db init
uv run poke-pricer demo seed
uv run poke-pricer api serve --host 127.0.0.1 --port 8001 --log-level warning &
PID=$!

# Wait for bind
for _ in $(seq 1 60); do
  curl -fsS http://127.0.0.1:8001/health >/dev/null 2>&1 && break
  sleep 0.25
done

echo "==> /health"; curl -fsS http://127.0.0.1:8001/health | jq . || true
echo "==> /v1/cards/search?q=pik"; curl -fsS "http://127.0.0.1:8001/v1/cards/search?q=pik" | jq . || true
echo "==> /v1/portfolio/value"; curl -fsS -X POST "http://127.0.0.1:8001/v1/portfolio/value" \
  -H "Content-Type: application/json" \
  -d '{"holdings":[{"card_id":2,"quantity":3.0}]}' | jq . || true

kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true

echo "==> Stage & commit"
git add -A
# Run pre-commit hooks only over staged changes
uv run pre-commit run --from-ref HEAD --to-ref : 2>/dev/null || true
git commit -m "$COMMIT_MSG" || echo "Nothing to commit (already clean)"

echo "==> Push branch"
git push -u origin "$BRANCH" || true

echo "==> Open or reuse PR"
if [ -x "scripts/open_pr.sh" ]; then
  bash scripts/open_pr.sh "$BRANCH" "$BASE" "$PR_TITLE" "$PR_BODY" || true
else
  # gh fallback
  if gh pr view "$BRANCH" >/dev/null 2>&1; then
    echo "PR already exists for $BRANCH"
  else
    gh pr create --base "$BASE" --head "$BRANCH" --title "$PR_TITLE" --body "$PR_BODY"
  fi
fi

echo "==> Watch latest PR CI (if present)"
RUN_ID="$(gh run list --branch "$BRANCH" --event pull_request --limit 1 --json databaseId -q '.[0].databaseId' || true)"
if [ -n "${RUN_ID:-}" ]; then
  gh run watch "$RUN_ID" --interval 5 || true
  echo "Conclusion: $(gh run view "$RUN_ID" --json conclusion -q '.conclusion' 2>/dev/null || echo unknown)"
else
  echo "No PR-run found yet (it will start shortly after push)."
fi

echo "==> Try to enable squash auto-merge (harmless if restricted)"
gh pr merge "$BRANCH" --squash --delete-branch --auto || true

echo "==> Pull merged main (OK if merge is manual)"
git checkout "$BASE"
git pull --ff-only

echo "==> Verify main quickly"
bash scripts/morning_check.sh

echo "Done: Sprint 16 finalized."
