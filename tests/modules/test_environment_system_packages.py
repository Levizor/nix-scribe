import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import NixWriter
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.packages import (
    DiscoveredPackage,
    PackageManager,
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
    assert ir == {"packages": [], "unmapped": []}


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
    package_names = [pkg.name for pkg in ir["packages"]]

    assert "docker" not in package_names
    assert "bat" in package_names
    assert "ripgrep" in package_names
    assert ir["unmapped"] == ["custom-tool"]


def test_system_packages_mapper_empty():
    assert system_packages.map(None) is None
    assert system_packages.map({}) is None
    assert system_packages.map({"packages": [], "unmapped": []}) is None


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

    ir = {
        "packages": [bat, spotify, rg],
        "unmapped": ["custom-cli"],
    }

    fragment = system_packages.map(ir)
    assert isinstance(fragment, ConfigFragment)
    assert fragment.name == "system-packages"
    assert "environment.systemPackages" in fragment.options

    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "environment.systemPackages = with pkgs; [" in output
    assert "bat /* from debian:batcat */" in output
    assert "ripgrep" in output
    assert "spotify /* from aur */" in output
    assert "# unmapped: custom-cli" in output


def test_system_packages_mapper_unmapped_only():
    ir = {
        "packages": [],
        "unmapped": ["orphan-tool"],
    }

    fragment = system_packages.map(ir)
    assert isinstance(fragment, ConfigFragment)
    assert "environment.systemPackages" in fragment.options

    nix_file = NixFile("configuration")
    nix_file.add_fragment(fragment)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "environment.systemPackages = with pkgs; [" in output
    assert "# unmapped: orphan-tool" in output
