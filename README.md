# Pokémon Pricer

A production-grade platform for Pokémon card pricing, signals, and backtesting.

This repository follows the **WSL2 + `uv`** workflow, strict typing (`mypy`), lint/format (`ruff`), and reproducible tests (`pytest`). It includes **stateful resumption** files so our sprints can continue exactly where we left off.

## Quickstart (WSL2 + zsh + uv)

- Install prerequisites (build tools), install `uv`.
- `uv venv && uv sync`
- Quality gates: `uv run ruff check . && uv run ruff format . && uv run mypy . && uv run pytest -q`
- Try the CLI: `uv run poke-pricer --help`

## Structure

.
├── src/poke_pricer/ # Package
│ ├── cli.py # Typer CLI entry
│ ├── config.py # Pydantic Settings (env-based)
│ ├── logging_config.py # Logging setup
│ ├── init.py
│ └── main.py
├── tests/ # Tests (pytest)
├── docs/
│ ├── INSTRUCTIONS.md # Team instruction set
│ ├── PROJECT_STATE.json # Stateful resume data (authoritative)
│ ├── PROJECT_LOG.md # Sprint log
│ ├── README.md # Docs index
│ └── adr/ # Architecture decisions
├── .github/workflows/ci.yml # CI (ready once pushed)
├── .env.example # Env variables (fill in .env)
├── pyproject.toml # Project metadata / deps (with uv dev-deps)
├── ruff.toml, mypy.ini # Quality gates config
├── CHANGELOG.md
└── README.md

## Next

- After these files exist in this project’s “Files” area, we’ll initialize the GitHub repo and push, including adding your SRS/PRD/Architecture/Backtesting/Signals artifacts under `docs/requirements/`.
