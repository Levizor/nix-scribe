import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.packages import (
    AptManager,
    DiscoveredPackage,
    InstallReason,
    clear_package_managers,
    register_package_manager,
    set_package_resolver,
)
from nix_scribe.lib.parsers.apt import AptHistoryPackage, AptHistoryRecord
from tests.mocks.mock_resolver import MockPackageResolver

SAMPLE_STATUS = """
Package: ripgrep
Status: install ok installed
Priority: optional
Section: utils
Architecture: amd64
Version: 14.1.0-1

Package: batcat
Status: install ok installed
Priority: optional
Section: utils
Architecture: amd64
Version: 0.24.0

Package: libssl3
Status: install ok installed
Priority: optional
Section: libs
Architecture: amd64
Version: 3.0.13

Package: removed-tool
Status: deinstall ok config-files
Priority: optional
Section: utils
Architecture: amd64
Version: 1.0.0
"""

SAMPLE_EXTENDED_STATES = """
Package: ripgrep
Architecture: amd64
Auto-Installed: 0

Package: batcat
Architecture: amd64
Auto-Installed: 0

Package: libssl3
Architecture: amd64
Auto-Installed: 1

Package: removed-tool
Architecture: amd64
Auto-Installed: 0
"""


@pytest.fixture(autouse=True)
def cleanup():
    clear_package_managers()
    register_package_manager(AptManager)
    set_package_resolver(None)
    yield
    clear_package_managers()
    set_package_resolver(None)


def test_apt_manager_detect(tmp_path):
    context = SystemContext(root=tmp_path)
    manager = AptManager()
    assert manager.detect(context) is False

    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(SAMPLE_STATUS)

    assert manager.detect(context) is True


def test_apt_manager_discover_packages_debian(tmp_path):
    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(SAMPLE_STATUS)

    ext_file = tmp_path / "var/lib/apt/extended_states"
    ext_file.parent.mkdir(parents=True)
    ext_file.write_text(SAMPLE_EXTENDED_STATES)

    context = SystemContext(root=tmp_path)
    manager = AptManager()
    packages = manager.discover_packages(context)

    assert len(packages) == 3
    assert packages == [
        DiscoveredPackage(
            name="batcat", repository="debian", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="libssl3", repository="debian", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="ripgrep", repository="debian", reason=InstallReason.EXPLICIT
        ),
    ]


def test_apt_manager_discover_packages_ubuntu(tmp_path):
    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(SAMPLE_STATUS)

    ext_file = tmp_path / "var/lib/apt/extended_states"
    ext_file.parent.mkdir(parents=True)
    ext_file.write_text(SAMPLE_EXTENDED_STATES)

    os_release = tmp_path / "etc/os-release"
    os_release.parent.mkdir(parents=True)
    os_release.write_text('ID=ubuntu\nID_LIKE="debian"\n')

    context = SystemContext(root=tmp_path)
    manager = AptManager()
    packages = manager.discover_packages(context)

    assert len(packages) == 3
    assert packages == [
        DiscoveredPackage(
            name="batcat", repository="ubuntu", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="libssl3", repository="ubuntu", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="ripgrep", repository="ubuntu", reason=InstallReason.EXPLICIT
        ),
    ]


def test_apt_manager_integration_with_system_context(tmp_path):
    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(SAMPLE_STATUS)

    ext_file = tmp_path / "var/lib/apt/extended_states"
    ext_file.parent.mkdir(parents=True)
    ext_file.write_text(SAMPLE_EXTENDED_STATES)

    resolver = MockPackageResolver(
        mapping={
            ("debian", "batcat"): "bat",
            ("debian", "libssl3"): "openssl",
            ("debian", "ripgrep"): "ripgrep",
        }
    )
    set_package_resolver(resolver)

    context = SystemContext(root=tmp_path)
    assert isinstance(context.package_manager, AptManager)

    state = context.packages
    assert len(state.resolved) == 3
    assert state.has("bat")
    assert state.has("ripgrep")
    assert state.has("openssl")
    assert len(state.unclaimed) == 3
    assert {p.name for p in state.unclaimed} == {"bat", "openssl", "ripgrep"}


def test_apt_manager_discover_packages_with_metapackages(tmp_path):
    extended_states = """
Package: my-cli
Auto-Installed: 0

Package: firefox
Auto-Installed: 1

Package: libgtk-3-0
Auto-Installed: 1
"""
    dpkg_status = """
Package: ubuntu-desktop
Status: install ok installed
Section: metapackages
Recommends: firefox, libgtk-3-0, uninstalled-app

Package: my-cli
Status: install ok installed
Section: utils

Package: firefox
Status: install ok installed
Section: web

Package: libgtk-3-0
Status: install ok installed
Section: libs

Package: uninstalled-app
Status: deinstall ok config-files
Section: web
"""
    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(dpkg_status)

    ext_file = tmp_path / "var/lib/apt/extended_states"
    ext_file.parent.mkdir(parents=True)
    ext_file.write_text(extended_states)

    context = SystemContext(root=tmp_path)
    manager = AptManager()
    packages = manager.discover_packages(context)

    assert packages == [
        DiscoveredPackage(
            name="firefox", repository="debian", reason=InstallReason.PREINSTALLED
        ),
        DiscoveredPackage(
            name="libgtk-3-0", repository="debian", reason=InstallReason.DEPENDENCY
        ),
        DiscoveredPackage(
            name="my-cli", repository="debian", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="ubuntu-desktop", repository="debian", reason=InstallReason.DEPENDENCY
        ),
    ]


def test_apt_manager_discover_packages_from_history_log(tmp_path):
    dpkg_status = """
Package: curl
Status: install ok installed
Section: web

Package: fastfetch
Status: install ok installed
Section: utils

Package: ca-certificates
Status: install ok installed
Section: misc

Package: libssl3
Status: install ok installed
Section: libs
"""
    extended_states = """
Package: ca-certificates
Auto-Installed: 1

Package: libssl3
Auto-Installed: 1
"""
    history_log = """
Start-Date: 2026-10-14  17:04:43
Commandline: apt-get install -y curl fastfetch
Install: ca-certificates:amd64 (20260601, automatic), fastfetch:amd64 (2.57.1), curl:amd64 (8.18.0)
End-Date: 2026-10-14  17:04:46
"""
    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(dpkg_status)

    ext_file = tmp_path / "var/lib/apt/extended_states"
    ext_file.parent.mkdir(parents=True)
    ext_file.write_text(extended_states)

    hist_file = tmp_path / "var/log/apt/history.log"
    hist_file.parent.mkdir(parents=True)
    hist_file.write_text(history_log)

    context = SystemContext(root=tmp_path)
    manager = AptManager()
    packages = manager.discover_packages(context)

    assert packages == [
        DiscoveredPackage(
            name="ca-certificates",
            repository="debian",
            reason=InstallReason.PREINSTALLED,
        ),
        DiscoveredPackage(
            name="curl", repository="debian", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="fastfetch", repository="debian", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="libssl3", repository="debian", reason=InstallReason.DEPENDENCY
        ),
    ]


def test_apt_manager_discover_packages_multiple_history_logs(tmp_path):
    dpkg_status = """
Package: ripgrep
Status: install ok installed
Section: utils

Package: bat
Status: install ok installed
Section: utils
"""
    history_log_old = """
Start-Date: 2026-10-14  10:00:00
Commandline: apt install ripgrep
Install: ripgrep:amd64 (14.1.0)
End-Date: 2026-10-14  10:00:05
"""
    history_log_new = """
Start-Date: 2026-10-14  12:00:00
Commandline: apt install bat
Install: bat:amd64 (0.24.0)
End-Date: 2026-10-14  12:00:05
"""
    status_file = tmp_path / "var/lib/dpkg/status"
    status_file.parent.mkdir(parents=True)
    status_file.write_text(dpkg_status)

    hist_old = tmp_path / "var/log/apt/history.log.1"
    hist_old.parent.mkdir(parents=True)
    hist_old.write_text(history_log_old)

    hist_new = tmp_path / "var/log/apt/history.log"
    hist_new.write_text(history_log_new)

    context = SystemContext(root=tmp_path)
    manager = AptManager()
    packages = manager.discover_packages(context)

    assert packages == [
        DiscoveredPackage(
            name="bat", repository="debian", reason=InstallReason.EXPLICIT
        ),
        DiscoveredPackage(
            name="ripgrep", repository="debian", reason=InstallReason.EXPLICIT
        ),
    ]


def test_apt_manager_extract_explicit_packages():
    records = [
        AptHistoryRecord(
            commandline="apt install ripgrep bat libssl3",
            install=[
                AptHistoryPackage(name="ripgrep", version="14.1.0"),
                AptHistoryPackage(name="bat", version="0.24.0"),
                AptHistoryPackage(name="libssl3", version="3.0", flags=("automatic",)),
            ],
        ),
        AptHistoryRecord(
            commandline="apt remove bat",
            remove=[AptHistoryPackage(name="bat", version="0.24.0")],
        ),
        AptHistoryRecord(
            commandline="apt-mark manual htop tmux",
        ),
        AptHistoryRecord(
            commandline="apt-mark auto tmux",
        ),
    ]

    explicit = AptManager._extract_explicit_packages(records)
    assert explicit == {"ripgrep", "htop"}
