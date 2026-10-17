import subprocess
from pathlib import Path

import pytest

from nix_scribe.lib.context import ElevationRequest, SystemContext

GENERIC_SYSTEM_ROOT = Path(__file__).parent.parent / "systems/generic"


@pytest.fixture
def context():
    return SystemContext(GENERIC_SYSTEM_ROOT)


def test_root_path(context):
    assert context.root_path("/etc/passwd") == GENERIC_SYSTEM_ROOT / "etc/passwd"
    assert context.root_path("usr/bin/bash") == GENERIC_SYSTEM_ROOT / "usr/bin/bash"


def test_path_exists(context):
    assert context.path_exists("/etc/passwd") is True
    assert context.path_exists("/nonexistent") is False


def test_find_executable_path(context):
    bash_path = context.find_executable_path("bash")
    assert bash_path is not None
    assert bash_path.endswith("/bin/bash")

    assert context.find_executable_path("nonexistent-binary") is None


def test_root_command_args(context):
    cmd = ["ls", "/etc/sudoers", "-la"]
    prefixed = context._root_command_args(cmd)

    assert prefixed[0] == "ls"
    assert prefixed[1] == str(GENERIC_SYSTEM_ROOT / "etc/sudoers")
    assert prefixed[2] == "-la"


def test_root_command_args_no_prefix_non_paths(context):
    cmd = ["grep", "root", "/etc/passwd"]
    prefixed = context._root_command_args(cmd)

    assert prefixed[0] == "grep"
    assert prefixed[1] == "root"
    assert prefixed[2] == str(GENERIC_SYSTEM_ROOT / "etc/passwd")


def test_list_directory_full_paths(tmp_path):
    d = tmp_path / "etc/testdir"
    d.mkdir(parents=True)
    (d / "a.txt").write_text("a")
    (d / "b.txt").write_text("b")

    ctx = SystemContext(tmp_path)
    entries = ctx.list_directory("/etc/testdir")
    assert entries == ["a.txt", "b.txt"]

    full_entries = ctx.list_directory("/etc/testdir", full_paths=True)
    assert full_entries == ["/etc/testdir/a.txt", "/etc/testdir/b.txt"]


def test_read_bytes(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\xde\xad\xbe\xef")

    ctx = SystemContext(tmp_path)
    assert ctx.read_bytes("data.bin") == b"\xde\xad\xbe\xef"


def test_read_bytes_sudo(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=True)
    monkeypatch.setattr(
        ctx,
        "_run_command",
        lambda cmd, text=False: subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=b"\xca\xfe"
        ),
    )
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    assert ctx.read_bytes("protected.bin") == b"\xca\xfe"


def test_read_file_sudo(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=True)
    monkeypatch.setattr(
        ctx,
        "_run_command",
        lambda cmd, text=False: subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="root text content\n"
        ),
    )
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, encoding=None: (_ for _ in ()).throw(PermissionError("denied")),
    )
    assert ctx.read_file("protected.txt") == "root text content\n"


def test_list_directory_sudo(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=True)
    recorded_cmd = []

    def mock_run(cmd, text=False):
        recorded_cmd.extend(cmd)
        return subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout=".hidden\nfile1.txt\n"
        )

    monkeypatch.setattr(ctx, "_run_command", mock_run)
    monkeypatch.setattr(
        "os.listdir",
        lambda path: (_ for _ in ()).throw(PermissionError("denied")),
    )
    assert ctx.list_directory("protected_dir") == [".hidden", "file1.txt"]
    assert recorded_cmd == ["sudo", "ls", "-1A", "protected_dir"]


def test_elevation_request_raised(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=False)
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    with pytest.raises(ElevationRequest, match="Permission denied"):
        ctx.read_bytes("protected.bin")
