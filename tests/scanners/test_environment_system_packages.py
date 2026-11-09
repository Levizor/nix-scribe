import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import NixWriter
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import NixFragment
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
from nix_scribe.scanners.environment.system_packages import system_packages
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
    assert system_packages.scan(context) is None


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

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")
    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    output = nix_file.gettext()

    assert "docker" not in output
    assert "bat" in output
    assert "ripgrep" in output

    asset = next(iter(fragment.assets))
    assert "custom-tool # from aur:custom-tool" in asset.content


def test_system_packages_formatting(tmp_path):
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

    context = SystemContext(root=tmp_path)
    context.packages = PackageState(packages=[bat, spotify, rg], unmapped=[custom_cli])

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")
    assert isinstance(fragment, NixFragment)
    assert fragment.name == "system_packages"
    assert "environment" in fragment.options

    assert len(fragment.assets) == 1
    asset = next(iter(fragment.assets))
    assert asset.target_filename == "packages.log"
    assert "custom-cli # from debian:custom-cli" in asset.content
    assert "bat # from debian:batcat" in asset.content

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
    assert "bat # from debian:batcat" in output
    assert "ripgrep # from arch:ripgrep" in output
    assert "spotify # from aur:spotify" in output
    assert "# unmapped: custom-cli" not in output


def test_system_packages_unmapped_only(tmp_path):
    orphan_tool = DiscoveredPackage("orphan-tool", repository="aur")
    context = SystemContext(root=tmp_path)
    context.packages = PackageState(packages=[], unmapped=[orphan_tool])

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")
    assert isinstance(fragment, NixFragment)
    assert "environment" not in fragment.options

    assert len(fragment.assets) == 1
    asset = next(iter(fragment.assets))
    assert asset.target_filename == "packages.log"
    assert "orphan-tool # from aur:orphan-tool" in asset.content


def test_system_packages_divided_by_comments(tmp_path):
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

    context = SystemContext(root=tmp_path)
    context.packages = PackageState(packages=[curl, rg])

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")

    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "# User-installed packages" in output
    assert "ripgrep # from arch:ripgrep" in output
    assert "# Pre-installed distribution utilities (commented out by default)" in output
    assert "# curl # from debian:curl" in output


def test_system_packages_ignores_dependencies(tmp_path):
    libssl = ResolvedPackage(
        name="openssl",
        original=DiscoveredPackage(
            "libssl3", repository="debian", reason=InstallReason.DEPENDENCY
        ),
    )
    context = SystemContext(root=tmp_path)
    context.packages = PackageState(packages=[libssl])
    assert system_packages.scan(context) is None


def test_system_packages_unmapped_details_formatting(tmp_path):
    pkg1 = DiscoveredPackage(
        "custom1", repository="ppa:test", reason=InstallReason.EXPLICIT
    )
    pkg2 = DiscoveredPackage(
        "custom2", repository="debian", reason=InstallReason.PREINSTALLED
    )
    context = SystemContext(root=tmp_path)
    context.packages = PackageState(packages=[], unmapped=[pkg1, pkg2])

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")

    assert len(fragment.assets) == 1
    asset = next(iter(fragment.assets))
    assert "custom1 # from ppa:test:custom1" in asset.content
    assert "custom2 # from debian:custom2" in asset.content


def test_system_packages_full_report_generation(tmp_path):
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

    context = SystemContext(root=tmp_path)
    context.packages = state

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")

    asset = next(iter(fragment.assets))
    report = asset.content

    assert "User-installed packages:" in report
    assert "curl # from ubuntu:curl" in report
    assert "Pre-installed distribution utilities:" in report
    assert "nano # from ubuntu:nano" in report
    assert "Claimed packages:" in report
    assert "git # from ubuntu:git (claimed by programs.git)" in report
    assert "Excluded dependencies:" in report
    assert "openssl # from ubuntu:libssl3" in report
    assert "Unmapped packages:" in report
    assert "mytool # from ubuntu:mytool" in report


def test_system_packages_no_comment(tmp_path, monkeypatch):
    monkeypatch.setattr("nix_scribe.lib.nix_writer.args.no_comment", True)
    rg = ResolvedPackage(
        name="ripgrep",
        original=DiscoveredPackage(
            "ripgrep", repository="arch", reason=InstallReason.EXPLICIT
        ),
    )
    curl = ResolvedPackage(
        name="curl",
        original=DiscoveredPackage(
            "curl", repository="debian", reason=InstallReason.PREINSTALLED
        ),
    )
    context = SystemContext(root=tmp_path)
    context.packages = PackageState(packages=[rg, curl])

    mod = system_packages.scan(context)
    assert mod is not None
    fragment = mod.to_nix_fragment(name="system_packages")

    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "ripgrep" in output
    assert "# from" not in output
    assert "curl" not in output
    assert "#" not in output
