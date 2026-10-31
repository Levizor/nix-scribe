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
