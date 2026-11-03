import logging
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from nix_scribe.arguments import CLIArguments
from nix_scribe.logger import setup_logging
from nix_scribe.main import app

runner = CliRunner()


def test_setup_logging_creates_directory_and_writes_format(tmp_path: Path):
    log_file = tmp_path / "nested" / "output" / "nix-scribe.log"
    setup_logging(verbosity=1, mod_verbosity=1, log_file=log_file)

    assert log_file.exists()

    core_logger = logging.getLogger("nix_scribe.core")
    mod_logger = logging.getLogger("nix_scribe.modules.boot.kernel")

    core_logger.debug("Core debug trace")
    core_logger.info("Core test message")
    mod_logger.debug("Module debug trace")
    mod_logger.warning("Module warning message")

    content = log_file.read_text(encoding="utf-8")
    assert "DEBUG   [nix_scribe.core] Core debug trace" in content
    assert "INFO    [nix_scribe.core] Core test message" in content
    assert "DEBUG   [nix_scribe.modules.boot.kernel] Module debug trace" in content
    assert "WARNING [nix_scribe.modules.boot.kernel] Module warning message" in content


def test_setup_logging_debug_flag_configures_rich_handler():
    # Verbosity < 2: show_level and show_path are False
    setup_logging(verbosity=1, mod_verbosity=1)
    core_logger = logging.getLogger("nix_scribe")
    mod_logger = logging.getLogger("nix_scribe.modules")

    core_handler = core_logger.handlers[0]
    mod_handler = mod_logger.handlers[0]

    assert core_handler._log_render.show_level is False
    assert core_handler._log_render.show_path is False
    assert mod_handler._log_render.show_level is False
    assert mod_handler._log_render.show_path is False

    # Verbosity >= 2: show_level and show_path are True
    setup_logging(verbosity=2, mod_verbosity=2)
    core_handler = core_logger.handlers[0]
    mod_handler = mod_logger.handlers[0]

    assert core_handler._log_render.show_level is True
    assert core_handler._log_render.show_path is True
    assert mod_handler._log_render.show_level is True
    assert mod_handler._log_render.show_path is True


def test_cli_list_modules_does_not_create_log_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--list-modules"])
    assert result.exit_code == 0
    assert not (tmp_path / "nix-scribe.log").exists()


def test_cli_list_modules_tree_does_not_create_log_file(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["--list-modules-tree"])
    assert result.exit_code == 0
    assert not (tmp_path / "nix-scribe.log").exists()


def test_cli_no_log_file_flag(tmp_path: Path):
    out_dir = tmp_path / "nix-out"
    with patch("nix_scribe.main.NixScribe") as mock_nix_scribe:
        mock_nix_scribe.return_value.run.return_value = None
        result = runner.invoke(app, ["-o", str(out_dir), "--no-log-file"])
        assert result.exit_code == 0
        assert not (out_dir / "nix-scribe.log").exists()


def test_cli_default_log_file_in_output_directory(tmp_path: Path):
    out_dir = tmp_path / "nix-out"
    with patch("nix_scribe.main.NixScribe") as mock_nix_scribe:
        mock_nix_scribe.return_value.run.return_value = None
        result = runner.invoke(app, ["-o", str(out_dir)])
        assert result.exit_code == 0
        assert (out_dir / "nix-scribe.log").exists()


def test_cli_custom_log_file_flag(tmp_path: Path):
    out_dir = tmp_path / "nix-out"
    custom_log = tmp_path / "custom" / "run.log"
    with patch("nix_scribe.main.NixScribe") as mock_nix_scribe:
        mock_nix_scribe.return_value.run.return_value = None
        result = runner.invoke(app, ["-o", str(out_dir), "--log-file", str(custom_log)])
        assert result.exit_code == 0
        assert custom_log.exists()
        assert not (out_dir / "nix-scribe.log").exists()


def test_args_check_ignores_existing_log_file(tmp_path: Path):
    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True)
    (out_dir / "nix-scribe.log").write_text("dummy")

    args = CLIArguments(output_path=out_dir, log_file=out_dir / "nix-scribe.log")
    # Should not raise typer.Exit or prompt confirm since only the log file exists
    args.check()


def test_args_check_prompts_on_existing_files(tmp_path: Path):
    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True)
    (out_dir / "configuration.nix").write_text("# nix config")

    args = CLIArguments(output_path=out_dir, confirm=False)
    with patch("nix_scribe.arguments.confirm", return_value=False):
        import pytest
        import typer

        with pytest.raises(typer.Exit):
            args.check()
