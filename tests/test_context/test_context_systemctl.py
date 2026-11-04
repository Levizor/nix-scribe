from __future__ import annotations

from pathlib import Path

import pytest

from nix_scribe.lib.context import SystemContext

GENERIC_SYSTEM_ROOT = Path(__file__).parent.parent / "systems/generic"


@pytest.fixture
def system_context():
    return SystemContext(GENERIC_SYSTEM_ROOT)


def test_systemctl_is_enabled_via_alias(system_context):
    """Test service enabled via a base-directory symlink alias."""
    assert system_context.systemctl.is_enabled("sddm") is True
    assert system_context.systemctl.is_enabled("sddm.service") is True


def test_systemctl_is_enabled_via_wants(system_context):
    """Test service enabled via a target .wants directory."""
    assert system_context.systemctl.is_enabled("nginx") is True


def test_systemctl_template_service(system_context):
    """Test an instantiated template service."""
    assert system_context.systemctl.exists("getty@tty1") is True
    assert system_context.systemctl.is_enabled("getty@tty1.service") is True


def test_systemctl_masked_service(system_context):
    """Test that a masked service is treated as non-existent and disabled."""
    assert system_context.systemctl.exists("bluetooth") is False
    assert system_context.systemctl.is_enabled("bluetooth") is False


def test_systemctl_is_disabled(system_context):
    """Test a service that exists on disk but has no enablement symlinks."""
    assert system_context.systemctl.exists("gdm") is True
    assert system_context.systemctl.is_enabled("gdm") is False
    assert system_context.systemctl.is_disabled("gdm") is True


def test_systemctl_nonexistent(system_context):
    """Test a service that does not exist anywhere."""
    assert system_context.systemctl.exists("nonexistent-service") is False
    assert system_context.systemctl.is_enabled("nonexistent-service") is False
    assert system_context.systemctl.is_disabled("nonexistent-service") is False


def test_systemctl_elevation_fallback(monkeypatch, tmp_path):
    import subprocess

    from nix_scribe.lib.systemctl import Systemctl

    ctx = SystemContext(tmp_path, use_sudo=True)

    def mock_run(cmd, text=False):
        cmd_str = " ".join(cmd)
        if "test -e" in cmd_str:
            return subprocess.CompletedProcess(args=cmd, returncode=0)
        if "ls -1A" in cmd_str and "etc/systemd/system" in cmd_str:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="nginx.service\nmulti-user.target.wants\n",
            )
        if "ls -1A" in cmd_str and "multi-user.target.wants" in cmd_str:
            return subprocess.CompletedProcess(
                args=cmd, returncode=0, stdout="nginx.service\n"
            )
        if "test -h" in cmd_str:
            return subprocess.CompletedProcess(args=cmd, returncode=0)
        if "readlink" in cmd_str:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="/usr/lib/systemd/system/nginx.service\n",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="")

    monkeypatch.setattr(ctx, "_run_command", mock_run)
    monkeypatch.setattr(
        "os.listdir",
        lambda path: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(
        "os.readlink",
        lambda path: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(ctx, "path_exists", lambda path: True)

    ctl = Systemctl(ctx)
    assert ctl.exists("nginx") is True
    assert ctl.is_enabled("nginx") is True


def test_systemctl_elevation_request_without_sudo(monkeypatch, tmp_path):
    from nix_scribe.lib.context import ElevationRequest
    from nix_scribe.lib.systemctl import Systemctl

    ctx = SystemContext(tmp_path, use_sudo=False)
    monkeypatch.setattr(
        "os.listdir",
        lambda path: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(ctx, "path_exists", lambda path: True)

    with pytest.raises(ElevationRequest):
        Systemctl(ctx)


def test_systemctl_elevation_request_on_readlink(monkeypatch, tmp_path):
    from nix_scribe.lib.context import ElevationRequest
    from nix_scribe.lib.systemctl import Systemctl

    ctx = SystemContext(tmp_path, use_sudo=False)
    monkeypatch.setattr(ctx, "path_exists", lambda path: True)
    monkeypatch.setattr(ctx, "list_directory", lambda path: ["foo.service"])
    monkeypatch.setattr(ctx, "is_symlink", lambda path: True)

    def raise_elevation(path, recursive=False):
        raise ElevationRequest(path, "Permission denied")

    monkeypatch.setattr(ctx, "readlink", raise_elevation)

    with pytest.raises(ElevationRequest):
        Systemctl(ctx)
