import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import NixWriter
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.packages import (
    DiscoveredPackage,
    InstallReason,
    PackageManager,
    PackageState,
    ResolvedPackage,
    clear_package_managers,
    register_package_manager,
    set_package_resolver,
)
from nix_scribe.lib.registry import ModulePhase
from nix_scribe.modules.environment.system_packages import system_packages
from tests.mocks.mock_resolver import MockPackageResolver


@pytest.fixture(autouse=True)
def cleanup():
    clear_package_managers()
    set_package_resolver(None)
    yield
    clear_package_managers()
    set_package_resolver(None)


def test_system_packages_module_metadata():
    assert system_packages.name == "environment.system_packages"
    assert system_packages.phase == ModulePhase.LATE


def test_system_packages_scanner_empty(tmp_path):
    context = SystemContext(root=tmp_path)
    ir = system_packages.scan(context)
    assert isinstance(ir["packages"], PackageState)
    assert ir["packages"].unclaimed == []
    assert ir["packages"].unmapped == []


def test_system_packages_scanner_unclaimed_and_unmapped(tmp_path):
    class MockArchManager(PackageManager):
        name = "pacman"
        distro = "arch"

        def detect(self, context: SystemContext) -> bool:
            return True

        def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
            return [
                DiscoveredPackage("ripgrep", repository="arch"),
                DiscoveredPackage("batcat", repository="debian"),
                DiscoveredPackage("docker", repository="arch"),
                DiscoveredPackage("custom-tool", repository="aur"),
            ]

    register_package_manager(MockArchManager)

    resolver = MockPackageResolver(
        mapping={
            ("arch", "ripgrep"): "ripgrep",
            ("debian", "batcat"): "bat",
            ("arch", "docker"): "docker",
            ("aur", "custom-tool"): None,
        }
    )
    set_package_resolver(resolver)

    context = SystemContext(root=tmp_path)

    # Simulate specialized module claiming docker in Phase 50
    assert context.packages.claim("docker") is True

    ir = system_packages.scan(context)
    assert isinstance(ir["packages"], PackageState)
    package_names = [pkg.name for pkg in ir["packages"].unclaimed]

    assert "docker" not in package_names
    assert "bat" in package_names
    assert "ripgrep" in package_names
    assert ir["packages"].unmapped == [
        DiscoveredPackage("custom-tool", repository="aur")
    ]


def test_system_packages_mapper_empty():
    assert system_packages.map(None) is None
    assert system_packages.map({}) is None
    assert system_packages.map({"packages": PackageState.empty()}) is None


def test_system_packages_mapper_formatting():
    bat = ResolvedPackage(
        name="bat",
        original=DiscoveredPackage("batcat", repository="debian"),
    )
    spotify = ResolvedPackage(
        name="spotify",
        original=DiscoveredPackage("spotify", repository="aur"),
    )
    rg = ResolvedPackage(
        name="ripgrep",
        original=DiscoveredPackage("ripgrep", repository="arch"),
    )
    custom_cli = DiscoveredPackage("custom-cli", repository="debian")

    ir = {
        "packages": PackageState(packages=[bat, spotify, rg], unmapped=[custom_cli]),
    }

    fragment = system_packages.map(ir)
    assert isinstance(fragment, ConfigFragment)
    assert fragment.name == "system-packages"
    assert "environment.systemPackages" in fragment.options

    assert len(fragment.assets) == 1
    asset = next(iter(fragment.assets))
    assert asset.target_filename == "packages.log"
    assert "custom-cli (from debian:custom-cli)" in asset.content
    assert "bat (from debian:batcat)" in asset.content

    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "environment.systemPackages = with pkgs; [" in output
    assert (
        "# See packages.log for the full package mapping report and unmapped packages."
        in output
    )
    assert "bat /* from debian:batcat */" in output
    assert "ripgrep" in output
    assert "spotify /* from aur */" in output
    assert "# unmapped: custom-cli" not in output


def test_system_packages_mapper_unmapped_only():
    orphan_tool = DiscoveredPackage("orphan-tool", repository="aur")
    ir = {
        "packages": PackageState(packages=[], unmapped=[orphan_tool]),
    }

    fragment = system_packages.map(ir)
    assert isinstance(fragment, ConfigFragment)
    assert "environment.systemPackages" not in fragment.options

    assert len(fragment.assets) == 1
    asset = next(iter(fragment.assets))
    assert asset.target_filename == "packages.log"
    assert "orphan-tool (from aur:orphan-tool)" in asset.content


def test_system_packages_mapper_divided_by_comments():
    curl = ResolvedPackage(
        name="curl",
        original=DiscoveredPackage(
            "curl", repository="debian", reason=InstallReason.PREINSTALLED
        ),
    )
    rg = ResolvedPackage(
        name="ripgrep",
        original=DiscoveredPackage(
            "ripgrep", repository="arch", reason=InstallReason.EXPLICIT
        ),
    )

    ir = {
        "packages": PackageState(packages=[curl, rg]),
    }

    fragment = system_packages.map(ir)
    assert fragment is not None

    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "# User-installed packages" in output
    assert "ripgrep" in output
    assert "# Pre-installed distribution utilities (commented out by default)" in output
    assert "# curl" in output


def test_system_packages_mapper_ignores_dependencies():
    libssl = ResolvedPackage(
        name="openssl",
        original=DiscoveredPackage(
            "libssl3", repository="debian", reason=InstallReason.DEPENDENCY
        ),
    )
    ir = {
        "packages": PackageState(packages=[libssl]),
    }
    assert system_packages.map(ir) is None


def test_system_packages_mapper_unmapped_details_formatting():
    pkg1 = DiscoveredPackage(
        "custom1", repository="ppa:test", reason=InstallReason.EXPLICIT
    )
    pkg2 = DiscoveredPackage(
        "custom2", repository="debian", reason=InstallReason.PREINSTALLED
    )
    ir = {
        "packages": PackageState(packages=[], unmapped=[pkg1, pkg2]),
    }
    fragment = system_packages.map(ir)
    assert fragment is not None

    assert len(fragment.assets) == 1
    asset = next(iter(fragment.assets))
    assert "custom1 (from ppa:test:custom1)" in asset.content
    assert "custom2 (from debian:custom2)" in asset.content


def test_system_packages_full_report_generation():
    curl = ResolvedPackage(
        name="curl",
        original=DiscoveredPackage(
            "curl", repository="ubuntu", reason=InstallReason.EXPLICIT
        ),
    )
    git = ResolvedPackage(
        name="git",
        original=DiscoveredPackage(
            "git", repository="ubuntu", reason=InstallReason.EXPLICIT
        ),
    )
    nano = ResolvedPackage(
        name="nano",
        original=DiscoveredPackage(
            "nano", repository="ubuntu", reason=InstallReason.PREINSTALLED
        ),
    )
    libssl = ResolvedPackage(
        name="openssl",
        original=DiscoveredPackage(
            "libssl3", repository="ubuntu", reason=InstallReason.DEPENDENCY
        ),
    )
    unmapped_explicit = DiscoveredPackage(
        "mytool", repository="ubuntu", reason=InstallReason.EXPLICIT
    )

    state = PackageState(
        packages=[curl, git, nano, libssl], unmapped=[unmapped_explicit]
    )
    state.claim("git", by="programs.git")

    ir = {"packages": state}
    fragment = system_packages.map(ir)
    assert fragment is not None

    asset = next(iter(fragment.assets))
    report = asset.content

    assert "User-installed packages:" in report
    assert "curl (from ubuntu:curl)" in report
    assert "Pre-installed distribution utilities:" in report
    assert "nano (from ubuntu:nano)" in report
    assert "Claimed packages:" in report
    assert "git (from ubuntu:git) (claimed by programs.git)" in report
    assert "Excluded dependencies:" in report
    assert "openssl (from ubuntu:libssl3)" in report
    assert "Unmapped packages:" in report
    assert "mytool (from ubuntu:mytool)" in report
