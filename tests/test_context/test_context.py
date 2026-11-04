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


def test_path_exists_sudo(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=True)
    monkeypatch.setattr(
        Path,
        "stat",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(
        ctx,
        "_run_command",
        lambda cmd, text=False: subprocess.CompletedProcess(args=cmd, returncode=0),
    )
    assert ctx.path_exists("protected_file") is True

    def fail_run(cmd, text=False):
        raise RuntimeError("test -e failed")

    monkeypatch.setattr(ctx, "_run_command", fail_run)
    assert ctx.path_exists("protected_file") is False


def test_path_exists_elevation_request(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=False)
    monkeypatch.setattr(
        Path,
        "stat",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    with pytest.raises(ElevationRequest):
        ctx.path_exists("protected_file")


def test_is_symlink_elevation_request(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=False)
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    with pytest.raises(ElevationRequest):
        ctx.is_symlink("protected_link")


def test_find_executable_path(context):
    bash_path = context.find_executable_path("bash")
    assert bash_path is not None
    assert bash_path.endswith("/bin/bash")

    assert context.find_executable_path("nonexistent-binary") is None


def test_is_symlink(tmp_path):
    link = tmp_path / "link.txt"
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link.symlink_to(target)

    ctx = SystemContext(tmp_path)
    assert ctx.is_symlink("link.txt") is True
    assert ctx.is_symlink("target.txt") is False
    assert ctx.is_symlink("nonexistent") is False


def test_is_symlink_sudo(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=True)
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(
        ctx,
        "_run_command",
        lambda cmd, text=False: subprocess.CompletedProcess(args=cmd, returncode=0),
    )
    assert ctx.is_symlink("protected_link") is True

    def fail_run(cmd, text=False):
        raise RuntimeError("test -h failed")

    monkeypatch.setattr(ctx, "_run_command", fail_run)
    assert ctx.is_symlink("protected_link") is False


def test_readlink(tmp_path):
    link = tmp_path / "link.txt"
    target = tmp_path / "target.txt"
    target.write_text("hello")
    link.symlink_to("target.txt")

    ctx = SystemContext(tmp_path)
    assert ctx.readlink("link.txt") == "target.txt"


def test_readlink_sudo(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=True)
    monkeypatch.setattr(
        "os.readlink",
        lambda path: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(
        ctx,
        "_run_command",
        lambda cmd, text=False: subprocess.CompletedProcess(
            args=cmd, returncode=0, stdout="/usr/lib/systemd/system/foo.service\n"
        ),
    )
    assert ctx.readlink("protected_link") == "/usr/lib/systemd/system/foo.service"


def test_readlink_recursive(tmp_path):
    (tmp_path / "a").symlink_to("b")
    (tmp_path / "b").symlink_to("c")
    (tmp_path / "c").write_text("final")

    ctx = SystemContext(tmp_path)
    assert ctx.readlink("a", recursive=True) == "c"


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


def test_read_file_bytes(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\xde\xad\xbe\xef")

    ctx = SystemContext(tmp_path)
    assert ctx.read_file_bytes("data.bin") == b"\xde\xad\xbe\xef"


def test_read_file_bytes_sudo(monkeypatch, tmp_path):
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
    assert ctx.read_file_bytes("protected.bin") == b"\xca\xfe"


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
    assert recorded_cmd == ["sudo", "ls", "-1A", str(ctx.root_path("protected_dir"))]


def test_elevation_request_raised(monkeypatch, tmp_path):
    ctx = SystemContext(tmp_path, use_sudo=False)
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda self: (_ for _ in ()).throw(PermissionError("denied")),
    )
    with pytest.raises(ElevationRequest, match="Permission denied"):
        ctx.read_file_bytes("protected.bin")


def test_open_sqlite(tmp_path):
    import sqlite3

    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE users (name TEXT)")
    conn.execute("INSERT INTO users VALUES ('alice')")
    conn.commit()
    conn.close()

    ctx = SystemContext(tmp_path)
    with ctx.open_sqlite("test.db") as read_conn:
        cursor = read_conn.cursor()
        cursor.execute("SELECT name FROM users")
        assert cursor.fetchall() == [("alice",)]
