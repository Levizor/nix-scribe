import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.packages import (
    DiscoveredPackage,
    InstallReason,
    PacmanManager,
    clear_package_managers,
    register_package_manager,
    set_package_resolver,
)

SAMPLE_HTOP_DESC = """%NAME%
htop

%VERSION%
3.3.0-1

%BASE%
htop

%DESC%
Interactive process viewer

%REASON%
0

%DEPENDS%
ncurses
libnl
"""

SAMPLE_RIPGREP_DESC = """%NAME%
ripgrep

%VERSION%
14.1.0-1

%DESC%
fast line-oriented search tool
"""

SAMPLE_NCURSES_DESC = """%NAME%
ncurses

%VERSION%
6.4-1

%DESC%
System V Release 4.0 curses emulation library

%REASON%
1
"""

SAMPLE_BASE_DESC = """%NAME%
base

%VERSION%
3-2

%DESC%
Minimal package set to define a basic Arch Linux installation

%REASON%
0
"""


@pytest.fixture(autouse=True)
def cleanup():
    clear_package_managers()
    register_package_manager(PacmanManager)
    set_package_resolver(None)
    yield
    clear_package_managers()
    set_package_resolver(None)


def test_pacman_manager_detect(tmp_path):
    context = SystemContext(root=tmp_path)
    manager = PacmanManager()
    assert manager.detect(context) is False

    pacman_local = tmp_path / "var/lib/pacman/local"
    pacman_local.mkdir(parents=True)

    assert manager.detect(context) is True


def test_pacman_manager_discover_packages(tmp_path):
    local_dir = tmp_path / "var/lib/pacman/local"

    (local_dir / "htop-3.3.0-1").mkdir(parents=True)
    (local_dir / "htop-3.3.0-1/desc").write_text(SAMPLE_HTOP_DESC)

    (local_dir / "ripgrep-14.1.0-1").mkdir(parents=True)
    (local_dir / "ripgrep-14.1.0-1/desc").write_text(SAMPLE_RIPGREP_DESC)

    (local_dir / "ncurses-6.4-1").mkdir(parents=True)
    (local_dir / "ncurses-6.4-1/desc").write_text(SAMPLE_NCURSES_DESC)

    (local_dir / "base-3-2").mkdir(parents=True)
    (local_dir / "base-3-2/desc").write_text(SAMPLE_BASE_DESC)

    (local_dir / "ALPM_DB_VERSION").write_text("9\n")

    context = SystemContext(root=tmp_path)
    manager = PacmanManager()
    packages = manager.discover_packages(context)

    assert len(packages) == 4
    assert packages == [
        DiscoveredPackage(
            name="base", repository="arch", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="htop", repository="arch", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="ncurses", repository="arch", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="ripgrep", repository="arch", reason=InstallReason.EXPLICIT
        ),
    ]


def test_pacman_manager_system_context_detection(tmp_path):
    local_dir = tmp_path / "var/lib/pacman/local"
    (local_dir / "htop-3.3.0-1").mkdir(parents=True)
    (local_dir / "htop-3.3.0-1/desc").write_text(SAMPLE_HTOP_DESC)

    context = SystemContext(root=tmp_path)
    assert isinstance(context.package_manager, PacmanManager)
    assert context.package_manager.name == "pacman"
    assert context.package_manager.distro == "arch"


def test_pacman_manager_discover_packages_with_history(tmp_path):
    local_dir = tmp_path / "var/lib/pacman/local"

    (local_dir / "curl-8.23.0-1").mkdir(parents=True)
    (local_dir / "curl-8.23.0-1/desc").write_text("%NAME%\ncurl\n\n%REASON%\n1\n")

    (local_dir / "fastfetch-2.70.0-1").mkdir(parents=True)
    (local_dir / "fastfetch-2.70.0-1/desc").write_text(
        "%NAME%\nfastfetch\n\n%REASON%\n0\n"
    )

    (local_dir / "yyjson-0.13.0-1").mkdir(parents=True)
    (local_dir / "yyjson-0.13.0-1/desc").write_text("%NAME%\nyyjson\n\n%REASON%\n1\n")

    (local_dir / "sudo-1.9.15-1").mkdir(parents=True)
    (local_dir / "sudo-1.9.15-1/desc").write_text("%NAME%\nsudo\n\n%REASON%\n0\n")

    (local_dir / "base-3-2").mkdir(parents=True)
    (local_dir / "base-3-2/desc").write_text(SAMPLE_BASE_DESC)

    log_dir = tmp_path / "var/log"
    log_dir.mkdir(parents=True)
    (log_dir / "pacman.log").write_text(
        "[2026-10-25T00:03:55+0000] [ALPM] installed base (3-2)\n"
        "[2026-10-25T00:03:55+0000] [ALPM] installed sudo (1.9.15-1)\n"
        "[2026-10-31T19:59:16+0000] [PACMAN] Running 'pacman -Sy --noconfirm curl fastfetch'\n"
    )

    context = SystemContext(root=tmp_path)
    manager = PacmanManager()
    packages = manager.discover_packages(context)

    packages_by_name = {pkg.name: pkg.reason for pkg in packages}
    assert packages_by_name == {
        "base": InstallReason.DEPENDENCY,
        "curl": InstallReason.EXPLICIT,
        "fastfetch": InstallReason.EXPLICIT,
        "sudo": InstallReason.PREINSTALLED,
        "yyjson": InstallReason.DEPENDENCY,
    }


def test_pacman_manager_discover_packages_with_removed_and_asdeps(tmp_path):
    local_dir = tmp_path / "var/lib/pacman/local"

    (local_dir / "ripgrep-14.1.0-1").mkdir(parents=True)
    (local_dir / "ripgrep-14.1.0-1/desc").write_text("%NAME%\nripgrep\n\n%REASON%\n1\n")

    (local_dir / "bat-0.24.0-1").mkdir(parents=True)
    (local_dir / "bat-0.24.0-1/desc").write_text("%NAME%\nbat\n\n%REASON%\n0\n")

    log_dir = tmp_path / "var/log"
    log_dir.mkdir(parents=True)
    (log_dir / "pacman.log").write_text(
        "[2026-10-25T10:00:00+0000] [PACMAN] Running 'pacman -S ripgrep htop'\n"
        "[2026-10-26T10:00:00+0000] [PACMAN] Running 'pacman -R htop'\n"
        "[2026-10-27T10:00:00+0000] [PACMAN] Running 'pacman -D --asdeps ripgrep'\n"
    )

    context = SystemContext(root=tmp_path)
    manager = PacmanManager()
    packages = manager.discover_packages(context)

    packages_by_name = {pkg.name: pkg.reason for pkg in packages}
    assert packages_by_name == {
        "bat": InstallReason.PREINSTALLED,
        "ripgrep": InstallReason.DEPENDENCY,
    }


def test_pacman_manager_discover_packages_empty_log(tmp_path):
    local_dir = tmp_path / "var/lib/pacman/local"

    (local_dir / "vim-9.1-1").mkdir(parents=True)
    (local_dir / "vim-9.1-1/desc").write_text("%NAME%\nvim\n\n%REASON%\n0\n")

    (local_dir / "glibc-2.40-1").mkdir(parents=True)
    (local_dir / "glibc-2.40-1/desc").write_text("%NAME%\nglibc\n\n%REASON%\n1\n")

    log_dir = tmp_path / "var/log"
    log_dir.mkdir(parents=True)
    (log_dir / "pacman.log").write_text(
        "[2026-10-25T00:03:55+0000] [ALPM] installed vim (9.1-1)\n"
    )

    context = SystemContext(root=tmp_path)
    manager = PacmanManager()
    packages = manager.discover_packages(context)

    packages_by_name = {pkg.name: pkg.reason for pkg in packages}
    assert packages_by_name == {
        "vim": InstallReason.PREINSTALLED,
        "glibc": InstallReason.DEPENDENCY,
    }
