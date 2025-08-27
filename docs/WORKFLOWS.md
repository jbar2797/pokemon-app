# Team Workflows (MVP Phase)

> Always run project scripts with **bash**. From your repo root:
>
> ```bash
> bash scripts/morning_check.sh
> bash scripts/start_feature.sh <feature-branch-name>
> bash scripts/commit_and_open_pr.sh "<commit-msg>" "<PR title>" "<PR body>"
> ```

## Daily — Morning sanity on `main`

- `scripts/morning_check.sh`:
  - Fast-forwards `main`
  - Re-syncs env (`uv lock && uv sync --dev`)
  - Runs gates (`ruff`, `mypy`, `pytest`)
  - Runs API smoke (seeds demo DB and probes `/health`, `/v1/catalog/summary`, `/v1/reports/top-movers`)

## Start a feature

- `scripts/start_feature.sh feature/sXX-short-name`
  - Creates/resets branch from latest `origin/main`
  - Syncs env and runs gates

## Commit + Open PR

- `scripts/commit_and_open_pr.sh "<commit msg>" "<PR title>" "<PR body>"`
  - Stages, runs pre-commit, commits
  - Pushes branch
  - Opens PR via `scripts/open_pr.sh` (or falls back to `gh`)
  - Requests squash auto-merge

## Release Policy (MVP freeze)

- No GitHub Releases until MVP is approved.
- See `docs/RELEASE_POLICY.md`.
