import sqlite3

import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.packages import (
    DiscoveredPackage,
    DnfManager,
    InstallReason,
    clear_package_managers,
    register_package_manager,
    set_package_resolver,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_package_managers()
    register_package_manager(DnfManager)
    set_package_resolver(None)
    yield
    clear_package_managers()
    set_package_resolver(None)


def _create_rpmdb(path, packages: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE Name (key TEXT NOT NULL, hnum INTEGER, idx INTEGER)")
    for i, name in enumerate(packages):
        cursor.execute(
            "INSERT INTO Name (key, hnum, idx) VALUES (?, ?, ?)", (name, i, 0)
        )
    conn.commit()
    conn.close()


def _create_dnf_history(path, history_records: list[tuple[str, int, int]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE trans (id INTEGER PRIMARY KEY, state INTEGER)")
    cursor.execute("CREATE TABLE rpm (id INTEGER PRIMARY KEY, name TEXT)")
    cursor.execute(
        """
        CREATE TABLE trans_item (
            id INTEGER PRIMARY KEY,
            trans_id INTEGER,
            item_id INTEGER,
            action INTEGER,
            reason INTEGER
        )
        """
    )
    cursor.execute("INSERT INTO trans VALUES (1, 1)")

    for i, (name, action, reason) in enumerate(history_records):
        item_id = i + 1
        cursor.execute("INSERT INTO rpm VALUES (?, ?)", (item_id, name))
        cursor.execute(
            "INSERT INTO trans_item VALUES (?, 1, ?, ?, ?)",
            (i + 1, item_id, action, reason),
        )

    conn.commit()
    conn.close()


def test_dnf_manager_detect(tmp_path):
    context = SystemContext(root=tmp_path)
    manager = DnfManager()
    assert manager.detect(context) is False

    rpm_db = tmp_path / "var/lib/rpm/rpmdb.sqlite"
    _create_rpmdb(rpm_db, ["bash"])
    assert manager.detect(context) is True


def test_dnf_manager_detect_sysimage(tmp_path):
    context = SystemContext(root=tmp_path)
    manager = DnfManager()
    rpm_db = tmp_path / "usr/lib/sysimage/rpm/rpmdb.sqlite"
    _create_rpmdb(rpm_db, ["bash"])
    assert manager.detect(context) is True


def test_dnf_manager_discover_packages_with_history(tmp_path):
    rpm_db = tmp_path / "var/lib/rpm/rpmdb.sqlite"
    _create_rpmdb(rpm_db, ["htop", "libgit2", "glibc", "curl"])

    history_db = tmp_path / "var/lib/dnf/history.sqlite"
    _create_dnf_history(
        history_db,
        [
            ("htop", 1, 2),  # action=INSTALL, reason=USER (2)
            ("libgit2", 1, 1),  # action=INSTALL, reason=DEPENDENCY (1)
        ],
    )

    os_release = tmp_path / "etc/os-release"
    os_release.parent.mkdir(parents=True, exist_ok=True)
    os_release.write_text('ID=fedora\nVERSION_ID="41"\n')

    context = SystemContext(root=tmp_path)
    manager = DnfManager()
    packages = manager.discover_packages(context)

    assert packages == [
        DiscoveredPackage(
            name="curl", repository="fedora_41", reason=InstallReason.PREINSTALLED
        ),
        DiscoveredPackage(
            name="glibc", repository="fedora_41", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="htop", repository="fedora_41", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="libgit2", repository="fedora_41", reason=InstallReason.DEPENDENCY
        ),
    ]


def test_dnf_manager_discover_packages_without_history(tmp_path):
    rpm_db = tmp_path / "var/lib/rpm/rpmdb.sqlite"
    _create_rpmdb(rpm_db, ["glibc", "ripgrep"])

    os_release = tmp_path / "etc/os-release"
    os_release.parent.mkdir(parents=True, exist_ok=True)
    os_release.write_text("ID=fedora\nVERSION_ID=40\n")

    context = SystemContext(root=tmp_path)
    manager = DnfManager()
    packages = manager.discover_packages(context)

    assert packages == [
        DiscoveredPackage(
            name="glibc", repository="fedora_40", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="ripgrep", repository="fedora_40", reason=InstallReason.EXPLICIT
        ),
    ]


def test_dnf_manager_system_context_detection(tmp_path):
    rpm_db = tmp_path / "var/lib/rpm/rpmdb.sqlite"
    _create_rpmdb(rpm_db, ["bash"])

    context = SystemContext(root=tmp_path)
    assert isinstance(context.package_manager, DnfManager)
    assert context.package_manager.name == "dnf"
    assert context.package_manager.distro == "fedora"
