from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from . import __version__
from .analytics.backtest import backtest_momentum_topk
from .analytics.data_access import load_prices_df
from .analytics.signals import compute_signals
from .config import Settings
from .db import init_db
from .ingest.csv_ingest import ingest_csv
from .io.csv_io import export_prices_csv
from .logging_config import configure_logging
from .services.seed import seed_demo

app: typer.Typer = typer.Typer(help="Pokémon Pricer CLI")
console = Console()

# Sub-apps
db_app = typer.Typer(help="Database utilities")
demo_app = typer.Typer(help="Demo data")
prices_app = typer.Typer(help="Prices utilities")
signals_app = typer.Typer(help="Signal computation")
backtest_app = typer.Typer(help="Backtesting utilities")
ingest_app = typer.Typer(help="Ingestion pipelines")

app.add_typer(db_app, name="db")
app.add_typer(demo_app, name="demo")
app.add_typer(prices_app, name="prices")
app.add_typer(signals_app, name="signals")
app.add_typer(backtest_app, name="backtest")
app.add_typer(ingest_app, name="ingest")


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
def demo_seed_cmd() -> None:
    """Insert demo cards and ~30 days of price points."""
    num_cards, num_prices = seed_demo()
    console.print(f"[green]Seeded[/green] {num_cards} cards and {num_prices} price points.")


# ---- prices ----
@prices_app.command("export")  # type: ignore[misc]
def prices_export(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output CSV path",
            exists=False,
            file_okay=True,
            dir_okay=False,
        ),
    ],
) -> None:
    """Export prices (joined with cards) to CSV."""
    n = export_prices_csv(out)
    console.print(f"[green]Exported[/green] {n} rows to {out}")


# ---- signals ----
@signals_app.command("compute")  # type: ignore[misc]
def signals_compute(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output CSV path for signals",
            exists=False,
            file_okay=True,
            dir_okay=False,
        ),
    ],
) -> None:
    """Compute signals and export to CSV."""
    df = load_prices_df()
    if df.empty:
        console.print(
            "[yellow]No price data found. Seed or ingest first "
            "('poke-pricer demo seed' or 'poke-pricer ingest csv').[/yellow]"
        )
        raise typer.Exit(code=0)
    sig = compute_signals(df)
    out.parent.mkdir(parents=True, exist_ok=True)
    sig.to_csv(out, index=False)
    console.print(f"[green]Signals written[/green] to {out} ({len(sig)} rows).")


# ---- backtest ----
@backtest_app.command("momentum")  # type: ignore[misc]
def backtest_momentum(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output CSV path for backtest equity",
            exists=False,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    k: Annotated[int, typer.Option("--k", help="Top-K by momentum each day")] = 1,
    lookback: Annotated[
        int,
        typer.Option("--lookback", help="Momentum lookback days"),
    ] = 14,
) -> None:
    """Run a tiny cross-sectional momentum backtest and export equity curve to CSV."""
    df = load_prices_df()
    if df.empty:
        console.print(
            "[yellow]No price data found. Seed or ingest first "
            "('poke-pricer demo seed' or 'poke-pricer ingest csv').[/yellow]"
        )
        raise typer.Exit(code=0)
    bt = backtest_momentum_topk(df, lookback=lookback, top_k=k)
    out.parent.mkdir(parents=True, exist_ok=True)
    bt.to_csv(out, index=False)
    msg_tail = f" last_equity={bt['equity'].iloc[-1]:.4f}" if not bt.empty else ""
    console.print(f"[green]Backtest written[/green] to {out} ({len(bt)} rows).{msg_tail}")


# ---- ingest ----
@ingest_app.command("csv")  # type: ignore[misc]
def ingest_csv_cmd(
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            help="CSV path with columns: name,set_code,number,date,price[,source,rarity]",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    source: Annotated[
        str | None,
        typer.Option("--source", help="Default source name if not present in CSV"),
    ] = None,
) -> None:
    """Ingest a CSV file into the local database (idempotent on card_id,date,source)."""
    created, inserted, skipped = ingest_csv(file, default_source=source or "csv")
    console.print(
        "[green]Ingest complete[/green] "
        f"(cards_created≈{created}, prices_inserted={inserted}, skipped={skipped})."
    )


def main() -> None:
    app()


__all__ = ["app", "main"]
