from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_catalog_export(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Seed via CLI
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    out_csv = tmp_path / "catalog.csv"
    res = _runner().invoke(app, ["catalog", "export", "--out", str(out_csv)])
    assert res.exit_code == 0, res.stdout

    text = out_csv.read_text().strip().splitlines()
    assert len(text) >= 1  # header + row
    header = text[0].split(",")
    assert header == ["total_cards", "total_prices", "min_date", "max_date", "sources"]
