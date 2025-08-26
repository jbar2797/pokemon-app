from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_validate_and_dir_ingest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    root = tmp_path / "in"
    root.mkdir()

    good = root / "good.csv"
    bad = root / "bad.csv"

    good.write_text(
        "\n".join(
            [
                "name,set_code,number,date,price,source",
                "Eevee,SVI,81/198,2025-01-01,12.50,manual",
                "Eevee,SVI,81/198,2025-01-02,12.75,manual",
            ]
        )
    )
    # Missing price
    bad.write_text(
        "\n".join(
            [
                "name,set_code,number,date,price,source",
                "Eevee,SVI,81/198,2025-01-01,,manual",
            ]
        )
    )

    monkeypatch.setenv("POKEPRICER_SQLITE_PATH", str(db_path))

    # Validate good/bad
    assert _runner().invoke(app, ["ingest", "validate", "--file", str(good)]).exit_code == 0
    assert _runner().invoke(app, ["ingest", "validate", "--file", str(bad)]).exit_code == 0

    # Ingest dir
    res = _runner().invoke(app, ["ingest", "dir", "--path", str(root), "--source", "manual"])
    assert res.exit_code == 0, res.stdout

    # Export to verify 2 rows present
    out_csv = tmp_path / "export.csv"
    res = _runner().invoke(app, ["prices", "export", "--out", str(out_csv)])
    assert res.exit_code == 0, res.stdout
    lines = out_csv.read_text().strip().splitlines()
    assert len(lines) == 3
