from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from . import __version__
from .config import Settings
from .db import init_db
from .io.csv_io import export_prices_csv
from .logging_config import configure_logging
from .services.seed import seed_demo

app: typer.Typer = typer.Typer(help="Pokémon Pricer CLI")
console = Console()

# Sub-apps
db_app = typer.Typer(help="Database utilities")
demo_app = typer.Typer(help="Demo data")
prices_app = typer.Typer(help="Prices utilities")

app.add_typer(db_app, name="db")
app.add_typer(demo_app, name="demo")
app.add_typer(prices_app, name="prices")


@app.callback(invoke_without_command=False)  # type: ignore[misc]
def _bootstrap(ctx: typer.Context) -> None:
    """Initialize settings and logging for all commands."""
    settings = Settings()
    configure_logging(settings.log_level)
    ctx.obj = {"settings": settings}


@app.command()  # type: ignore[misc]
def version() -> None:
    """Show package version."""
    console.print(f"pokemon-pricer {__version__}")


@app.command()  # type: ignore[misc]
def check() -> None:
    """Run basic environment checks and print warnings (always exit 0)."""
    settings = Settings()
    configure_logging(settings.log_level)
    if not settings.data_dir.exists():
        console.print(
            f"[yellow]- Data dir not found: {settings.data_dir!s} "
            f"(this is OK; run 'poke-pricer init' to create it)[/yellow]"
        )
    console.print("[green]Environment OK[/green]")


@app.command()  # type: ignore[misc]
def init(
    dir: Annotated[
        Path | None,
        typer.Option(help="Create data/logs/artifacts under this dir (default: current directory)"),
    ] = None,
) -> None:
    """Create local project directories."""
    base = dir or Path(".")
    for sub in ("data", "logs", "artifacts"):
        p = base / sub
        p.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created[/green] {p}")
    console.print("[green]Initialization complete[/green]")


@app.command()  # type: ignore[misc]
def env() -> None:
    """Print sanitized environment settings."""
    s = Settings()
    for k, v in s.as_public_dict().items():
        console.print(f"{k} = {v}")


# ---- db ----
@db_app.command("init")  # type: ignore[misc]
def db_init() -> None:
    """Create local SQLite tables at POKEPRICER_SQLITE_PATH."""
    init_db()
    console.print("[green]Database initialized[/green]")


# ---- demo ----
@demo_app.command("seed")  # type: ignore[misc]
def demo_seed() -> None:
    """Insert demo cards and ~30 days of price points."""
    num_cards, num_prices = seed_demo()
    console.print(f"[green]Seeded[/green] {num_cards} cards and {num_prices} price points.")


# ---- prices ----
@prices_app.command("export")  # type: ignore[misc]
def prices_export(
    out: Annotated[
        Path,
        typer.Option("--out", help="Output CSV path", exists=False, file_okay=True, dir_okay=False),
    ],
) -> None:
    """Export prices (joined with cards) to CSV."""
    n = export_prices_csv(out)
    console.print(f"[green]Exported[/green] {n} rows to {out}")


def main() -> None:
    app()


__all__ = ["app", "main"]
