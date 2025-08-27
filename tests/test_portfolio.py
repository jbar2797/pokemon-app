from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_portfolio_and_watchlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Use a throwaway DB
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Seed demo data (includes Pikachu BASE 58/102 used below)
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    # Watchlist with one known card from demo data
    wl = tmp_path / "watch.csv"
    wl.write_text("name,set_code,number\nPikachu,BASE,58/102\n")

    out_watch = tmp_path / "watch_prices.csv"
    res_watch = _runner().invoke(
        app, ["portfolio", "watchlist", "--file", str(wl), "--out", str(out_watch)]
    )
    assert res_watch.exit_code == 0, res_watch.stdout

    df_w = pd.read_csv(out_watch)
    expected_watch_cols = {
        "card_id",
        "name",
        "set_code",
        "number",
        "source",
        "price",
        "date",
    }
    assert expected_watch_cols.issubset(set(df_w.columns))

    # Holdings with the same card
    h = tmp_path / "hold.csv"
    h.write_text("name,set_code,number,qty,cost_per_unit\nPikachu,BASE,58/102,2,5.00\n")

    out_port = tmp_path / "portfolio.csv"
    res_port = _runner().invoke(
        app, ["portfolio", "value", "--file", str(h), "--out", str(out_port)]
    )
    assert res_port.exit_code == 0, res_port.stdout

    df_p = pd.read_csv(out_port)
    must_have = {
        "name",
        "set_code",
        "number",
        "qty",
        "price",
        "date",
        "market_value",
        "cost_per_unit",
        "pnl",
        "pct_return",
    }
    assert must_have.issubset(set(df_p.columns))
