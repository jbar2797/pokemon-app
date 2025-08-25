from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner  # third-party

from poke_pricer.cli import app  # first-party


def test_version_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "pokemon-pricer" in result.stdout


def test_check_exits_ok() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0


def test_init_creates_dirs(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / "data").exists()
    assert (tmp_path / "logs").exists()
    assert (tmp_path / "artifacts").exists()
