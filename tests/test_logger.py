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


def test_setup_logging_overwrites_existing_log_file(tmp_path: Path):
    log_file = tmp_path / "nix-scribe.log"
    log_file.write_text("old log line that should be overwritten\n", encoding="utf-8")

    setup_logging(verbosity=1, mod_verbosity=1, log_file=log_file)
    logger = logging.getLogger("nix_scribe")
    logger.info("new log line")

    content = log_file.read_text(encoding="utf-8")
    assert "old log line" not in content
    assert "new log line" in content


def test_args_check_prompts_on_existing_log_file(tmp_path: Path):
    import pytest
    import typer

    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True)
    (out_dir / "nix-scribe.log").write_text("dummy")

    args = CLIArguments(
        output_path=out_dir, log_file=out_dir / "nix-scribe.log", confirm=False
    )
    with patch("nix_scribe.arguments.confirm", return_value=False):
        with pytest.raises(typer.Exit):
            args.check()

    with patch("nix_scribe.arguments.confirm", return_value=True):
        args.check()


def test_args_check_unwritable_output_directory(tmp_path: Path, monkeypatch):
    import os

    import pytest
    import typer

    out_dir = tmp_path / "readonly_output"
    out_dir.mkdir(parents=True)

    def mock_access(path, mode):
        if str(path) == str(out_dir) and mode == os.W_OK:
            return False
        return True

    monkeypatch.setattr(os, "access", mock_access)

    args = CLIArguments(output_path=out_dir)
    with pytest.raises(typer.BadParameter) as exc_info:
        args.check()

    assert "Output directory" in str(exc_info.value)
    assert str(out_dir) in str(exc_info.value)
    assert "is not writable" in str(exc_info.value)
    assert "sudo" in str(exc_info.value)
    assert "chown" in str(exc_info.value)
    assert "$USER:$USER" in str(exc_info.value)


def test_args_check_unwritable_parent_directory(tmp_path: Path, monkeypatch):
    import os

    import pytest
    import typer

    parent_dir = tmp_path / "readonly_parent"
    parent_dir.mkdir(parents=True)
    out_dir = parent_dir / "nested" / "nix-config"

    def mock_access(path, mode):
        if str(path) == str(parent_dir) and mode == os.W_OK:
            return False
        return True

    monkeypatch.setattr(os, "access", mock_access)

    args = CLIArguments(output_path=out_dir)
    with pytest.raises(typer.BadParameter) as exc_info:
        args.check()

    assert "Output directory" in str(exc_info.value)
    assert str(out_dir) in str(exc_info.value)
    assert "is not writable" in str(exc_info.value)
    assert "sudo" in str(exc_info.value)
    assert "chown" in str(exc_info.value)
    assert "$USER:$USER" in str(exc_info.value)


def test_cli_unwritable_output_directory(tmp_path: Path, monkeypatch):
    import os

    out_dir = tmp_path / "readonly_output"
    out_dir.mkdir(parents=True)

    def mock_access(path, mode):
        if str(path) == str(out_dir) and mode == os.W_OK:
            return False
        return True

    monkeypatch.setattr(os, "access", mock_access)

    result = runner.invoke(app, ["-o", str(out_dir)])
    assert result.exit_code != 0
    assert "is not writable" in result.output
    assert "sudo" in result.output
    assert "chown" in result.output
    assert "$USER:$USER" in result.output


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


def test_cli_aborted_run_does_not_create_log_file(tmp_path: Path):
    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True)
    (out_dir / "configuration.nix").write_text("# preexisting config")

    with patch("nix_scribe.arguments.confirm", return_value=False):
        result = runner.invoke(app, ["-o", str(out_dir)])
        assert result.exit_code == 1
        assert not (out_dir / "nix-scribe.log").exists()


def test_context_os_and_root_logging(tmp_path: Path, caplog):
    etc = tmp_path / "etc"
    etc.mkdir()
    (etc / "os-release").write_text('NAME="Fedora Linux"\nVERSION_ID="40"\n')

    with caplog.at_level(logging.DEBUG):
        from nix_scribe.lib.context import SystemContext

        ctx = SystemContext(tmp_path)

    assert f"Target root: {tmp_path}" in caplog.text
    assert "Detected target OS: Fedora Linux 40" in caplog.text
    assert ctx.os_info.get("VERSION_ID") == "40"


def test_context_sudo_elevation_logging(tmp_path: Path, caplog):
    from nix_scribe.lib.context import SystemContext

    ctx = SystemContext(tmp_path, use_sudo=True)
    with caplog.at_level(logging.DEBUG):
        res = ctx._with_elevation(
            "/etc/secret",
            unprivileged=lambda: (_ for _ in ()).throw(PermissionError()),
            privileged=lambda: "privileged_content",
        )
        assert res == "privileged_content"

    assert "Falling back to privileged access for /etc/secret" in caplog.text


def test_systemctl_trace_logging(tmp_path: Path, caplog):
    from nix_scribe.lib.context import SystemContext
    from nix_scribe.lib.systemctl import Systemctl

    svc_dir = tmp_path / "usr/lib/systemd/system"
    svc_dir.mkdir(parents=True)
    svc_file = svc_dir / "nginx.service"
    svc_file.write_text("[Unit]\nDescription=Nginx")

    wants_dir = tmp_path / "etc/systemd/system/multi-user.target.wants"
    wants_dir.mkdir(parents=True)
    (wants_dir / "nginx.service").symlink_to("/usr/lib/systemd/system/nginx.service")

    ctx = SystemContext(tmp_path)
    with caplog.at_level(logging.DEBUG):
        ctl = Systemctl(ctx)
        assert ctl.is_enabled("nginx") is True
        assert ctl.exists("nonexistent") is False

    assert "Scanning systemd units in /usr/lib/systemd/system" in caplog.text
    assert "Built systemctl state:" in caplog.text
    assert "systemctl.is_enabled(nginx) -> True" in caplog.text
    assert "systemctl.exists(nonexistent) -> False" in caplog.text


def test_package_claims_and_pkgmap_trace_logging(caplog):
    from nix_scribe.lib.packages.models import (
        DiscoveredPackage,
        InstallReason,
        PackageState,
        ResolvedPackage,
    )
    from nix_scribe.lib.packages.pkgmap_resolver import PkgmapPackageResolver

    git_pkg = ResolvedPackage(
        "git", DiscoveredPackage("git", "arch", InstallReason.EXPLICIT)
    )
    state = PackageState(packages=[git_pkg])

    with caplog.at_level(logging.DEBUG):
        claimed = state.claim("git", by="programs.git")
        assert claimed is True
        unclaimed = state.claim("vim", by="programs.vim")
        assert unclaimed is False

    assert "Package 'git' claimed by programs.git" in caplog.text
    assert (
        "Package 'vim' not present on system; ignoring claim from programs.vim"
        in caplog.text
    )

    # Test PkgmapPackageResolver batch log
    resolver = PkgmapPackageResolver()
    disc_pkgs = [DiscoveredPackage("curl", "arch", InstallReason.EXPLICIT)]
    with caplog.at_level(logging.DEBUG):
        resolved, unmapped = resolver.resolve_many(disc_pkgs)

    assert "Batch resolving 1 packages across 1 repositories" in caplog.text
    assert "Resolution completed:" in caplog.text
