from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_alerts_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    csv_path = tmp_path / "prices.csv"
    out_csv = tmp_path / "alerts.csv"
    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    csv_path.write_text(
        "\n".join(
            [
                "name,set_code,number,date,price,source",
                "Eevee,SVI,81/198,2025-01-01,10.00,manual",
                "Eevee,SVI,81/198,2025-01-02,12.00,manual",
            ]
        )
    )

    assert _runner().invoke(app, ["db", "init"]).exit_code == 0
    res = _runner().invoke(app, ["ingest", "csv", "--file", str(csv_path), "--source", "manual"])
    assert res.exit_code == 0, res.stdout

    res = _runner().invoke(
        app, ["alerts", "scan", "--out", str(out_csv), "--threshold", "0.05", "--lookback", "7"]
    )
    assert res.exit_code == 0, res.stdout
    text = out_csv.read_text().strip().splitlines()
    assert len(text) >= 2  # header + at least one anomaly
    assert text[0].split(",") == [
        "card_id",
        "name",
        "set_code",
        "number",
        "source",
        "price",
        "return_1d",
        "flag",
        "date",
    ]
