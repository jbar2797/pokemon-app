# ADR 0001 — Architecture & Tooling Baseline

**Status:** Accepted — 2025-08-25

## Context
We need a reproducible Python stack aligned with the team's instruction set (WSL2 + `uv`), with strong quality gates and CI. The product requires data ingestion, pricing models, signal generation, and backtesting.

## Decision
- **Language/Runtime:** Python ≥ 3.11
- **Env/Deps/Tasks:** `uv` (venv, locking, task execution)
- **CLI:** Typer (Click-based) for developer UX
- **Config:** `pydantic-settings` reading `.env` (prefix `POKEPRICER_`)
- **Lint/Format:** Ruff
- **Types:** mypy (strict)
- **Tests:** pytest (+ hypothesis optional)
- **CI:** GitHub Actions (runs quality gates + tests)
- **Docs & Governance:** Markdown docs in `/docs`, ADRs in `/docs/adr`, CHANGELOG, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY

## Consequences
- Deterministic local and CI installs via `uv`.
- Enforced code quality from day one.
- Easy on-ramp for contributors with a single CLI and clear runbooks.
