import logging
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

logger = logging.getLogger(__name__)


class InstallReason(str, Enum):
    EXPLICIT = "explicit"
    PREINSTALLED = "preinstalled"
    DEPENDENCY = "dependency"


@dataclass(frozen=True)
class DiscoveredPackage:
    name: str
    repository: str
    reason: InstallReason = InstallReason.EXPLICIT

    @property
    def is_explicit(self) -> bool:
        return self.reason == InstallReason.EXPLICIT

    @property
    def is_preinstalled(self) -> bool:
        return self.reason == InstallReason.PREINSTALLED

    @property
    def is_dependency(self) -> bool:
        return self.reason == InstallReason.DEPENDENCY


@dataclass(frozen=True)
class ResolvedPackage:
    name: str
    original: DiscoveredPackage

    @property
    def original_name(self) -> str:
        return self.original.name

    @property
    def repository(self) -> str:
        return self.original.repository

    @property
    def reason(self) -> InstallReason:
        return self.original.reason

    @property
    def is_explicit(self) -> bool:
        return self.original.is_explicit

    @property
    def is_preinstalled(self) -> bool:
        return self.original.is_preinstalled

    @property
    def is_dependency(self) -> bool:
        return self.original.is_dependency


class PackageState:
    def __init__(
        self,
        packages: list[ResolvedPackage],
        unmapped: list[DiscoveredPackage] | None = None,
    ) -> None:
        self._packages = packages
        self._unmapped = sorted(unmapped or [], key=lambda p: p.name)
        self._claimed: dict[str, str | None] = {}

    @property
    def resolved(self) -> list[ResolvedPackage]:
        """All resolved packages discovered on the system."""
        return self._packages

    @property
    def packages(self) -> list[ResolvedPackage]:
        """Alias for resolved packages."""
        return self._packages

    @property
    def unmapped(self) -> list[DiscoveredPackage]:
        """Discovered packages that could not be mapped to Nixpkgs."""
        return self._unmapped

    @property
    def claimed(self) -> set[str]:
        """Set of package attribute names claimed by specialized modules."""
        return set(self._claimed.keys())

    @cached_property
    def by_attribute(self) -> dict[str, ResolvedPackage]:
        return {pkg.name: pkg for pkg in self._packages}

    @property
    def unclaimed(self) -> list[ResolvedPackage]:
        """Resolved packages not claimed by any specialized module."""
        return [
            pkg for attr, pkg in self.by_attribute.items() if attr not in self._claimed
        ]

    def has(self, attribute_name: str) -> bool:
        """Module API: check if a package exists on the system."""
        return attribute_name in self.by_attribute

    def claim(self, *attribute_names: str, by: str | None = None) -> bool:
        """Claims one or more packages if present so they won't be emitted in systemPackages.

        Returns True if at least one package was present and claimed, False otherwise.
        """
        any_claimed = False
        for attribute_name in attribute_names:
            if self.has(attribute_name):
                self._claimed[attribute_name] = by
                logger.debug(
                    "Package '%s' claimed by %s", attribute_name, by or "unknown"
                )
                any_claimed = True
            else:
                logger.debug(
                    "Package '%s' not present on system; ignoring claim from %s",
                    attribute_name,
                    by or "unknown",
                )
        return any_claimed

    def claimed_by(self, attribute_name: str) -> str | None:
        """Returns the module that claimed the package, if known."""
        return self._claimed.get(attribute_name)

    def is_claimed(self, attribute_name: str) -> bool:
        return attribute_name in self._claimed

    def get_unclaimed(self) -> list[ResolvedPackage]:
        """Alias for unclaimed property."""
        return self.unclaimed

    @classmethod
    def empty(cls) -> "PackageState":
        return cls(packages=[], unmapped=[])
