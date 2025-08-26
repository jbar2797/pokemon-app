# Project Log

## 2025-08-25 – Sprint 0: Repository bootstrap
- Created baseline Python project with `uv`, strict typing, linting, tests, CI workflow.
- Added state files (`PROJECT_STATE.json`, `PROJECT_LOG.md`, `CHANGELOG.md`, `INSTRUCTIONS.md`).
- Implemented minimal CLI (`poke-pricer`) with `version`, `check`, `init`, `env`.
- Established ADR #0001 for architecture/tooling choices.
- Next: populate `docs/requirements/` with SRS/PRD/Architecture/Backtesting/Signals when pushing to GitHub.

## 2025-08-26T01:24:52Z — Sprint-2 Completed (chg-0002)

**Step:** s2-analytics-signals-backtest
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 9a32714

### Scope delivered
- Analytics package:
  - `analytics/data_access.py` — load joined prices into a DataFrame
  - `analytics/signals.py` — returns, SMAs, momentum
  - `analytics/backtest.py` — simple cross-sectional momentum (top‑K) backtest
- CLI:
  - `poke-pricer signals compute --out <csv>`
  - `poke-pricer backtest momentum --out <csv> --k <int> --lookback <days>`
- Tests:
  - `tests/test_analytics.py` (signals + backtest end‑to‑end)
- Tooling:
  - Ruff line‑length and closure fixes
  - mypy stability (typed join + targeted ignores)
  - CI green on push

### Notes/decisions
- Avoided SQLAlchemy typed‑ORM relationships in Sprint 2; used explicit joins for stability.
- Kept type coverage strict; suppressions are narrow and documented.

## 2025-08-26T02:34:18Z — Sprint-3 Completed (chg-0003)

**Step:** s3-ingestion-csv-upsert
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** c1ebcf8

### Scope delivered
- DB: uniqueness & indexes for cards/prices.
- Ingestion: CSV → SQLite with idempotent upserts on (card_id, date, source).
- CLI: `poke-pricer ingest csv --file <path> [--source <name>]`.
- Tests: ingestion idempotency + export header check.
- CI: green.

### Notes
- Kept ORM model simple (no relationships) to minimize typing friction in SA 2.x.
- Future: bulk ingestion, schema validation, and source adapters.
