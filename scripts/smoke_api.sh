#!/usr/bin/env bash
set -Eeuo pipefail

# -------- Config (with sane defaults) --------
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8001}"
LOG_LEVEL="${LOG_LEVEL:-warning}"

# Use uv's Python to avoid system python dependency
PP="uv run python -c 'import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))'"

# -------- Helpers --------
cleanup() {
  if [[ -n "${PID:-}" ]]; then
    kill "${PID}" 2>/dev/null || true
    wait "${PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# -------- Repo root --------
REPO="${REPO:-$HOME/projects/pokemon-app}"
cd "$REPO"

# -------- Seed demo data --------
uv run python -m poke_pricer db init
uv run python -m poke_pricer demo seed

# -------- Start API (module form is most reliable across shells) --------
uv run python -m poke_pricer api serve \
  --host "${HOST}" \
  --port "${PORT}" \
  --log-level "${LOG_LEVEL}" &
PID=$!

# -------- Readiness loop (don’t query before bind) --------
for _ in $(seq 1 60); do
  if curl -fsS "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

# -------- Probe & pretty-print --------
echo "==> HEALTH"
curl -fsS "http://${HOST}:${PORT}/health" \
| bash -lc "$PP"
echo

echo "==> CATALOG SUMMARY"
curl -fsS "http://${HOST}:${PORT}/v1/catalog/summary" \
| bash -lc "$PP"
echo

echo "==> TOP MOVERS (k=2)"
curl -fsS "http://${HOST}:${PORT}/v1/reports/top-movers?k=2" \
| bash -lc "$PP"
echo

echo "==> Smoke OK"
