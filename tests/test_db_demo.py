from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_db_init_and_demo_seed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    r = _runner().invoke(app, ["db", "init"])
    assert r.exit_code == 0, r.stdout

    r = _runner().invoke(app, ["demo", "seed"])
    assert r.exit_code == 0, r.stdout

    assert db_path.exists(), "SQLite DB file should exist after seeding"
