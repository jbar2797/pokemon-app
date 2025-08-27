from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from poke_pricer.cli import app


def _runner() -> CliRunner:
    return CliRunner()


def test_notify_slack_dry_run(tmp_path: Path) -> None:
    csv = tmp_path / "alerts.csv"
    csv.write_text(
        "\n".join(
            [
                "card_id,name,set_code,number,source,price,return_1d,flag,date",
                "1,Eevee,SVI,81/198,csv,12.75,0.05,spike,2025-01-02",
            ]
        )
    )
    res = _runner().invoke(app, ["notify", "slack", "--file", str(csv), "--dry-run"])
    assert res.exit_code == 0, res.stdout
    assert "DRY-RUN Slack message" in res.stdout
