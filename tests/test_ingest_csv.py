from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def _write_csv(p: Path) -> None:
    p.write_text(
        "\n".join(
            [
                "name,set_code,number,date,price,source",
                "Eevee,SVI,81/198,2025-01-01,12.50,manual",
                "Eevee,SVI,81/198,2025-01-02,12.75,manual",
            ]
        )
    )


def test_ingest_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    csv_path = tmp_path / "prices.csv"
    export_csv = tmp_path / "export.csv"
    _write_csv(csv_path)

    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # First import
    res = _runner().invoke(app, ["ingest", "csv", "--file", str(csv_path), "--source", "manual"])
    assert res.exit_code == 0, res.stdout

    # Export should have 2 rows + header
    res = _runner().invoke(app, ["prices", "export", "--out", str(export_csv)])
    assert res.exit_code == 0, res.stdout
    lines = export_csv.read_text().strip().splitlines()
    assert len(lines) == 3
    expected_header = [
        "card_id",
        "name",
        "set_code",
        "number",
        "date",
        "source",
        "price",
    ]
    assert lines[0].split(",") == expected_header

    # Second import is idempotent
    res = _runner().invoke(app, ["ingest", "csv", "--file", str(csv_path), "--source", "manual"])
    assert res.exit_code == 0, res.stdout

    # Re-export: still 2 data rows
    res = _runner().invoke(app, ["prices", "export", "--out", str(export_csv)])
    assert res.exit_code == 0, res.stdout
    lines2 = export_csv.read_text().strip().splitlines()
    assert len(lines2) == 3
