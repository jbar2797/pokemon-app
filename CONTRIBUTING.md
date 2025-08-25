# Contributing

## Prerequisites
- WSL2 (Ubuntu), zsh, oh-my-zsh + powerlevel10k (recommended).
- Python 3.11+ managed with **uv**.
- `git` and `pre-commit`.

## Setup
```bash
uv venv
uv sync
pre-commit install

## Quality Gates

uv run ruff check .
uv run ruff format .
uv run mypy .
uv run pytest -q

## Branching & commits

Use Conventional Commits, e.g., feat: add TCGPlayer client.

Feature branches: feature/<short-kebab>.

PRs require passing quality gates and tests.
