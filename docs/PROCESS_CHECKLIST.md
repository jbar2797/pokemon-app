# Process Checklist (Sprint Gates)

**We do not advance a sprint unless ALL gates are green.**

## Pre-sprint gate
- [ ] Define goals, scope, acceptance criteria.
- [ ] Update `docs/PROJECT_STATE.json` with `current_sprint`, `current_step_id`.
- [ ] Create/adjust tasks/blocks.

## During sprint
- [ ] Code quality gates pass locally: `ruff`, `mypy`, `pytest`, `pre-commit`.
- [ ] Update docs (README, design notes) as features land.

## Sprint close-out
- [ ] CI green on main for the sprint changes.
- [ ] Update `docs/PROJECT_LOG.md` with date, step, scope, notes.
- [ ] Update `docs/PROJECT_STATE.json` with `last_changeset_id`, flags (e.g., `analytics_ready`).
- [ ] Update `CHANGELOG.md` with a “chg-####” entry.
- [ ] Ensure all external docs (SRS, PRD, Architecture, Backtesting, Signals) are committed under `docs/requirements/`.
- [ ] Tag release if appropriate (semver or `sprint-#` tags).
