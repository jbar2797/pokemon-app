#!/usr/bin/env bash
# scripts/smoke_api.sh
# Run a local API smoke test using bash (not zsh).

set -Eeuo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8001}"
REPO_DIR="${REPO_DIR:-$HOME/projects/pokemon-app}"

cd "$REPO_DIR"

# Ensure environment is in sync
uv lock >/dev/null
uv sync --dev >/dev/null

# Free the port if it's in use
if command -v lsof >/dev/null 2>&1; then
  lsof -tiTCP:$PORT -sTCP:LISTEN | xargs -r kill || true
fi
pkill -f "uvicorn .*${PORT}" 2>/dev/null || true

# Seed demo data
uv run poke-pricer db init
uv run poke-pricer demo seed

# Start the API (direct uvicorn to avoid console-script lookup quirks)
uv run uvicorn poke_pricer.api.app:app \
  --host "$HOST" --port "$PORT" --log-level warning &
PID=$!

cleanup() {
  kill "$PID" >/dev/null 2>&1 || true
  wait "$PID" 2>/dev/null || true
}
trap cleanup EXIT

# Readiness loop (10 seconds max)
for _ in $(seq 1 40); do
  if curl -fsS "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

echo "HEALTH:"
curl -fsS "http://${HOST}:${PORT}/health"; echo

echo "CATALOG:"
curl -fsS "http://${HOST}:${PORT}/v1/catalog/summary"; echo

echo "TOP MOVERS (k=2):"
curl -fsS "http://${HOST}:${PORT}/v1/reports/top-movers?k=2"; echo

echo "Smoke test OK."
