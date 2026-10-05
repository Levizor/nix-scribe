from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from nix_scribe.lib.packages.models import DiscoveredPackage

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext


class PackageManager(ABC):
    name: str
    distro: str

    @abstractmethod
    def detect(self, context: SystemContext) -> bool:
        """Returns True if this package manager state files are present on disk."""
        pass

    @abstractmethod
    def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
        """Parses native distro state files into a list of DiscoveredPackage instances."""
        pass


_REGISTERED_PACKAGE_MANAGERS: list[type[PackageManager]] = []


def register_package_manager(pm_cls: type[PackageManager]) -> None:
    """Registers a PackageManager subclass for target detection."""
    if pm_cls not in _REGISTERED_PACKAGE_MANAGERS:
        _REGISTERED_PACKAGE_MANAGERS.append(pm_cls)


def get_registered_package_managers() -> list[type[PackageManager]]:
    """Returns a copy of all registered PackageManager subclasses."""
    return list(_REGISTERED_PACKAGE_MANAGERS)


def clear_package_managers() -> None:
    """Clears all registered PackageManager subclasses (used in tests)."""
    _REGISTERED_PACKAGE_MANAGERS.clear()
