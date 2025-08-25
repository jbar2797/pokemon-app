from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from . import __version__
from .config import Settings
from .logging_config import configure_logging

app: typer.Typer = typer.Typer(help="Pokémon Pricer CLI")
console = Console()


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

    # Warn but do not fail if the data directory is missing.
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


def main() -> None:
    app()


__all__ = ["app", "main"]
