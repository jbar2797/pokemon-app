from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_reports_daily(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "bundle"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Seed demo data then produce daily bundle
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0
    res = _runner().invoke(app, ["reports", "daily", "--out", str(out_dir), "--k", "3"])
    assert res.exit_code == 0, res.stdout

    # Files exist
    assert (out_dir / "catalog_summary.csv").exists()
    assert (out_dir / "top_movers.csv").exists()
    # latest_prices.csv may be empty but should be written
    assert (out_dir / "latest_prices.csv").exists()
