import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.packages import (
    DiscoveredPackage,
    PackageManager,
    ResolvedPackage,
    clear_package_managers,
    get_registered_package_managers,
    register_package_manager,
    set_package_resolver,
)
from tests.mocks.mock_resolver import MockPackageResolver


@pytest.fixture(autouse=True)
def cleanup():
    clear_package_managers()
    set_package_resolver(None)
    yield
    clear_package_managers()
    set_package_resolver(None)


def test_package_manager_registry():
    class DummyPackageManager(PackageManager):
        name = "dummy"
        distro = "generic"

        def detect(self, context: SystemContext) -> bool:
            return True

        def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
            return [DiscoveredPackage("nano", distro="generic")]

    register_package_manager(DummyPackageManager)
    assert DummyPackageManager in get_registered_package_managers()

    clear_package_managers()
    assert get_registered_package_managers() == []


def test_system_context_packages_empty_when_no_pm(tmp_path):
    context = SystemContext(root=tmp_path)
    assert context.packages.packages == []
    assert context.packages.unmapped == []


def test_system_context_packages_discovery_and_resolution(tmp_path):
    class MockArchManager(PackageManager):
        name = "pacman"
        distro = "arch"

        def detect(self, context: SystemContext) -> bool:
            return context.path_exists("var/lib/pacman")

        def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
            return [
                DiscoveredPackage("ripgrep", distro=self.distro),
                DiscoveredPackage("bat", distro=self.distro),
                DiscoveredPackage("unmapped-tool", distro=self.distro),
            ]

    register_package_manager(MockArchManager)

    resolver = MockPackageResolver(
        mapping={
            ("arch", "ripgrep"): "ripgrep",
            ("arch", "bat"): ResolvedPackage(
                name="bat", original_name="bat", repository="arch", category="apps"
            ),
            ("arch", "unmapped-tool"): None,
        }
    )
    set_package_resolver(resolver)

    context = SystemContext(root=tmp_path)
    pacman_db = tmp_path / "var" / "lib" / "pacman"
    pacman_db.mkdir(parents=True)

    packages = context.packages
    assert len(packages.packages) == 2
    assert packages.has("ripgrep")
    assert packages.has("bat")
    assert packages.unmapped == ["unmapped-tool"]

    # Verify cached return
    assert context.packages is packages
