# Changelog

All notable changes to this project will be documented here.

## [0.1.0] - 2025-08-25
### Added
- Sprint 0 scaffold with `uv` workflow, quality gates, CI, and state files.
- Minimal Typer CLI, typed settings, logging config.
- ADR #0001 documenting architecture/tooling choices.

## [0.1.0-chg-0003] - 2025-08-26
### Added
- CSV ingestion pipeline with idempotent upserts (SQLite).
- CLI command `ingest csv` with tests and CI.
### Changed
- DB models: uniqueness + indexes to support ingestion guarantees.

## [0.1.0-chg-0004] - 2025-08-26
### Added
- CSV validation (Pydantic) for ingestion rows.
- Directory ingestion (`poke-pricer ingest dir`).
- Catalog summary + CSV export (`poke-pricer catalog summary|export`).

### Fixed
- SQL result handling (mypy-safe: `one()`, `one_or_none()`); robust distinct source normalization.

### Tooling
- mypy: narrow override for CLI decorators only; strict typing everywhere else.
