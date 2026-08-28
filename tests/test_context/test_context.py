from pathlib import Path

import pytest

from nix_scribe.lib.context import SystemContext

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
