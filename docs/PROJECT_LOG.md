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

## 2025-08-26T03:26:10Z — Sprint-4 Completed (chg-0004)

**Step:** s4-validation-catalog
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 056e3f2

### Scope delivered
- Ingestion validation with Pydantic schema (`ingest/schema.py`).
- Folder ingestion (`ingest dir`) with cumulative counts.
- Catalog summary (`catalog summary` & `catalog export`), SQL counts, date range, sources.
- Mypy/ruff hardened; CI green (mypy override limited to `poke_pricer.cli` decorators).

### Notes/decisions
- Used mypy-safe SQL result accessors (`one()`, `one_or_none()`) and robust distinct normalization.
- Kept CLI typing strict elsewhere; `misc` disabled only for CLI decorators in `mypy.ini`.

## 2025-08-26T20:05:03Z — Sprint-5 In Progress (chg-0005)

**Step:** s5-top-movers-report
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 05de0fd

### Scope
- Report: `reports/top_movers.py` — compute top movers by windowed return.
- CLI: `poke-pricer catalog top-movers --window <days> --top <k> [--out <csv>]`.
- Tests: coverage for export and terminal view.
- CI: green on feature branch.

## 2025-08-26T22:23:06Z — Sprint-5 Completed (chg-0005)

**Step:** s5-top-movers
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 7db5863

### Scope delivered
-  — compute daily winners/losers (top-K by 1‑day return).
- CLI: .
- Tests: .
- Docs: README usage. CI green.

### Notes/decisions
- Reuse existing price pipeline; keep ORM simple to maintain typing stability.

## 2025-08-26T22:23:33Z — Sprint-5 Completed (chg-0005)

**Step:** s5-top-movers
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 7db5863

### Scope delivered
-  — compute daily winners/losers (top-K by 1‑day return).
- CLI: .
- Tests: .
- Docs: README usage. CI green.

### Notes/decisions
- Reuse existing price pipeline; keep ORM simple to maintain typing stability.

## 2025-08-26T22:32:07Z — Sprint-5 Completed (chg-0005)

**Step:** s5-top-movers
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 7db5863

### Scope delivered
- `analytics/movers.py` — compute daily winners/losers (top-K by 1-day return).
- CLI: `poke-pricer movers top --out <csv> [--k N] [--date YYYY-MM-DD]`.
- Tests: `tests/test_movers.py`.
- Docs: README usage. CI green.

### Notes/decisions
- Reuse existing price pipeline; keep ORM simple to maintain typing stability.

## 2025-08-26T22:38:36Z — Sprint-5 Completed (chg-0005)

**Step:** s5-top-movers
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 6f857ec

### Scope delivered
- `analytics/movers.py` — compute daily winners/losers (top‑K by 1‑day return).
- CLI: `poke-pricer movers top --out <csv> [--k N] [--date YYYY-MM-DD]`.
- Tests: `tests/test_movers.py`.
- Docs: README usage. CI green.

### Notes/decisions
- Reuse the existing price pipeline; keep ORM simple to maintain typing stability.

## 2025-08-26T23:23:58Z — Sprint-6 Completed (chg-0006)

**Step:** s6-daily-reports
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 1714ef8

### Scope delivered
- `reports/daily.py` — writes `catalog_summary.csv`, `top_movers.csv`, `latest_prices.csv`.
- CLI: `poke-pricer reports daily --out <dir> [--k N] [--date YYYY-MM-DD]`.
- Tests: `tests/test_reports_daily.py`.
- CI: `.github/workflows/daily-reports.yml` (manual + scheduled).

### Notes/decisions
- Reused existing analytics/csv pipeline; kept CLI typing strict and line-length ≤100.

## 2025-08-27T00:20:30Z — Sprint-7 Completed (chg-0007)

**Step:** s7-alerts
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 8f2d020

### Scope delivered
- `reports/anomalies.py` — scan for 1‑day spikes and rolling new highs/lows.
- CLI: `poke-pricer alerts scan --out <csv> [--threshold F] [--lookback N] [--date YYYY-MM-DD]`.
- Tests: `tests/test_alerts.py`.
- CI: `.github/workflows/alerts.yml` (manual + scheduled) to publish alerts artifact.

### Notes/decisions
- Kept analytics pure Pandas; emit CSV for downstream email/Slack in later sprints.

## 2025-08-27T00:56:28Z — Sprint-9 Completed (chg-0009)

**Step:** s9-packaging-release
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 07c4a74

### Scope delivered
-  verified (wheel + sdist).
- GitHub Actions release workflow (tag push -> build & attach artifacts).
- Release tagging process documented.

### Notes/decisions
- Kept packaging simple (wheel + sdist); PyPI publish deferred until credentials are ready.

## 2025-08-27T02:48:56Z — Sprint-12 Completed (chg-0012)

**Step:** s12-coverage
**Repo:** https://github.com/jbar2797/pokemon-app.git
**Commit:** 4d13d01

### Scope delivered
- CI: coverage gating workflow (≥85%) and artifact upload of coverage.xml.
- Local pytest/coverage config;  added as dev dependency.
- Packaging: switched  license to SPDX string; .

### Notes
- Workflow intentionally lacks `workflow_dispatch`; it runs on push/PR to reduce manual triggers.
