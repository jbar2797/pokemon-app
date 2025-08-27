from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_qa_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    out_dir = tmp_path / "qa"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Seed demo data then produce QA bundle
    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0

    res = _runner().invoke(
        app,
        ["qa", "bundle", "--out", str(out_dir), "--stale-days", "30"],
    )
    assert res.exit_code == 0, res.stdout

    assert (out_dir / "qa_summary.csv").exists()
    assert (out_dir / "qa_duplicates.csv").exists()
    assert (out_dir / "qa_stale_cards.csv").exists()
