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

## Sprint 4 – Validation, Directory Ingest, Catalog

~~~bash
# Validate a CSV file (schema: name,set_code,number,date,price[,source,rarity])
uv run poke-pricer ingest validate --file data/prices.csv

# Ingest all CSVs from a folder (non-recursive), counting created/inserted/skipped
uv run poke-pricer ingest dir --path data --source csv

# Print catalog summary (total cards/prices, date range, sources)
uv run poke-pricer catalog summary

# Export summary to CSV
uv run poke-pricer catalog export --out artifacts/catalog_summary.csv
~~~

## Sprint 5 – Top Movers

```bash
# Write top-5 winners & losers for the latest day
uv run poke-pricer movers top --out artifacts/top_movers.csv --k 5

# For a specific date
uv run poke-pricer movers top --out artifacts/top_movers_2025-02-02.csv --k 5 --date 2025-02-02
card_id,name,set_code,number,source,price,return_1d,date,bucket

## Sprint 5 – Top Movers

```bash
# Write top-5 winners & losers for the latest day
uv run poke-pricer movers top --out artifacts/top_movers.csv --k 5

# For a specific date
uv run poke-pricer movers top --out artifacts/top_movers_2025-02-02.csv --k 5 --date 2025-02-02
card_id,name,set_code,number,source,price,return_1d,date,bucket
