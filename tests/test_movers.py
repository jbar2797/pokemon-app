from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_movers_top_from_seed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    out_csv = tmp_path / "movers.csv"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Prepare DB with demo data (≈30 days)
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    res = _runner().invoke(app, ["movers", "top", "--out", str(out_csv), "--k", "3"])
    assert res.exit_code == 0, res.stdout
    text = out_csv.read_text().strip().splitlines()
    assert len(text) >= 2  # header + rows
    header = text[0].split(",")
    assert header == [
        "card_id",
        "name",
        "set_code",
        "number",
        "source",
        "price",
        "return_1d",
        "date",
        "bucket",
    ]
