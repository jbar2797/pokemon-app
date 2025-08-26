from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from .analytics.backtest import backtest_momentum_topk
from .analytics.data_access import load_prices_df
from .analytics.signals import compute_signals
from .catalog.stats import catalog_summary_df, export_catalog_csv
from .config import Settings
from .db import init_db
from .ingest.csv_ingest import ingest_csv, ingest_dir, validate_csv
from .io.csv_io import export_prices_csv
from .services.seed import seed_demo

console = Console()
app = typer.Typer(no_args_is_help=True)

db_app = typer.Typer()
demo_app = typer.Typer()
prices_app = typer.Typer()
signals_app = typer.Typer()
backtest_app = typer.Typer()
ingest_app = typer.Typer()
catalog_app = typer.Typer()

app.add_typer(db_app, name="db")
app.add_typer(demo_app, name="demo")
app.add_typer(prices_app, name="prices")
app.add_typer(signals_app, name="signals")
app.add_typer(backtest_app, name="backtest")
app.add_typer(ingest_app, name="ingest")
app.add_typer(catalog_app, name="catalog")


@app.callback(invoke_without_command=False)
def _bootstrap() -> None:
    """Global initialization hook (reserved)."""
    return


@app.command()
def version() -> None:
    """Print tool version (package version)."""
    console.print("pokemon-pricer 0.1.0")


@app.command()
def check() -> None:
    """Basic environment sanity check."""
    console.print("Environment OK")


@app.command()
def init(
    dir: Annotated[
        Path | None,
        typer.Option(
            help="Create data/logs/artifacts here",
        ),
    ] = None,
) -> None:
    """Create local data/logs/artifacts directories."""
    base = dir or Path(".")
    for sub in ("data", "logs", "artifacts"):
        p = base / sub
        p.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created[/green] {p}")
    console.print("[green]Initialization complete[/green]")


@app.command()
def env() -> None:
    """Print sanitized environment variables."""
    s = Settings()
    for k, v in s.as_public_dict().items():
        console.print(f"{k} = {v}")


# ---- db ----
@db_app.command("init")
def db_init() -> None:
    """Create database tables."""
    init_db()
    console.print("[green]DB initialized[/green]")


# ---- demo ----
@demo_app.command("seed")
def demo_seed() -> None:
    """Insert demo cards and ~30 days of price points."""
    num_cards, num_prices = seed_demo()
    console.print(f"[green]Seeded[/green] {num_cards} cards and {num_prices} price points.")


# ---- prices ----
@prices_app.command("export")
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
    """Export prices joined with cards to CSV."""
    n = export_prices_csv(out)
    console.print(f"[green]Exported[/green] {n} rows to {out}")


# ---- signals ----
@signals_app.command("compute")
def signals_compute(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output CSV for signals",
            exists=False,
            file_okay=True,
            dir_okay=False,
        ),
    ],
) -> None:
    """Compute basic signals and write CSV."""
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
@backtest_app.command("momentum")
def backtest_momentum(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="Output CSV for equity",
            exists=False,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    k: Annotated[
        int,
        typer.Option(
            "--k",
            help="Top-K by momentum each day",
        ),
    ] = 1,
    lookback: Annotated[
        int,
        typer.Option(
            "--lookback",
            help="Momentum lookback days",
        ),
    ] = 14,
) -> None:
    """Run simple momentum backtest and write equity CSV."""
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
@ingest_app.command("csv")
def ingest_csv_cmd(
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            help="CSV with columns: name,set_code,number,date,price[,source,rarity]",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    source: Annotated[
        str | None,
        typer.Option(
            "--source",
            help="Default source name",
        ),
    ] = None,
) -> None:
    """Ingest a CSV file into the local database."""
    created, inserted, skipped = ingest_csv(file, default_source=source or "csv")
    console.print(
        "[green]Ingest complete[/green] "
        f"(cards_created={created}, prices_inserted={inserted}, skipped={skipped})."
    )


@ingest_app.command("validate")
def ingest_validate_cmd(
    file: Annotated[
        Path,
        typer.Option(
            "--file",
            help="CSV to validate",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
) -> None:
    """Validate a CSV against the expected schema."""
    valid, invalid = validate_csv(file)
    console.print(f"[green]Valid[/green]: {valid}, [yellow]Invalid[/yellow]: {invalid}")


@ingest_app.command("dir")
def ingest_dir_cmd(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            help="Folder containing CSV files",
            exists=True,
            file_okay=False,
            dir_okay=True,
        ),
    ],
    source: Annotated[
        str | None,
        typer.Option(
            "--source",
            help="Default source name",
        ),
    ] = None,
) -> None:
    """Ingest all CSV files from a directory (non-recursive)."""
    created, inserted, skipped = ingest_dir(path, default_source=source or "csv")
    console.print(
        "[green]Dir ingest complete[/green] "
        f"(cards_created={created}, prices_inserted={inserted}, skipped={skipped})."
    )


# ---- catalog ----
@catalog_app.command("summary")
def catalog_summary() -> None:
    """Print summary (counts, date range, sources)."""
    df = catalog_summary_df()
    if df.empty:
        console.print("[yellow]No data available.[/yellow]")
        return
    row = df.iloc[0].to_dict()
    console.print(
        "Summary: "
        f"cards={row['total_cards']} prices={row['total_prices']} "
        f"range={row['min_date']}..{row['max_date']} sources={row['sources']}"
    )


@catalog_app.command("export")
def catalog_export(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            help="CSV path for summary",
            exists=False,
            file_okay=True,
            dir_okay=False,
        ),
    ],
) -> None:
    """Export summary to CSV."""
    export_catalog_csv(out)
    console.print(f"[green]Catalog summary[/green] written to {out}")


def main() -> None:
    app()


__all__ = ["app", "main"]
