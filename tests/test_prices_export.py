from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_prices_export_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    out_csv = tmp_path / "export.csv"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    assert _runner().invoke(app, ["demo", "seed"]).exit_code == 0
    result = _runner().invoke(app, ["prices", "export", "--out", str(out_csv)])
    assert result.exit_code == 0, result.stdout

    assert out_csv.exists()
    text = out_csv.read_text().strip().splitlines()
    assert len(text) > 1  # header + at least one row
    expected_header = [
        "card_id",
        "name",
        "set_code",
        "number",
        "date",
        "source",
        "price",
    ]
    assert text[0].split(",") == expected_header
