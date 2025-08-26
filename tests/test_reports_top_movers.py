from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_top_movers_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Separate DB per test
    db_path = tmp_path / "test.db"
    out_csv = tmp_path / "top.csv"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Seed via CLI and export top movers
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    res = _runner().invoke(
        app, ["catalog", "top-movers", "--window", "14", "--top", "5", "--out", str(out_csv)]
    )
    assert res.exit_code == 0, res.stdout
    assert out_csv.exists()
    header = out_csv.read_text().splitlines()[0].split(",")
    assert header == [
        "window_days",
        "rank",
        "card_id",
        "name",
        "set_code",
        "number",
        "last_date",
        "last_price",
        "ret_window",
    ]


def test_top_movers_print(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    res = _runner().invoke(app, ["catalog", "top-movers", "--window", "7", "--top", "3"])
    assert res.exit_code == 0, res.stdout
