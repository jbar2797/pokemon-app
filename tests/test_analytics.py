from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_signals_and_backtest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    signals_csv = tmp_path / "signals.csv"
    bt_csv = tmp_path / "bt.csv"

    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Init DB, seed demo data
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    # Compute signals
    res = _runner().invoke(app, ["signals", "compute", "--out", str(signals_csv)])
    assert res.exit_code == 0, res.stdout
    assert signals_csv.exists()
    head = signals_csv.read_text().splitlines()[0].split(",")
    # minimal header check
    assert {"card_id", "date", "price", "ret"}.issubset(set(head))

    # Backtest momentum
    res = _runner().invoke(
        app,
        [
            "backtest",
            "momentum",
            "--out",
            str(bt_csv),
            "--k",
            "1",
            "--lookback",
            "14",
        ],
    )
    assert res.exit_code == 0, res.stdout
    assert bt_csv.exists()
    lines = bt_csv.read_text().strip().splitlines()
    assert len(lines) >= 2  # header + one row
