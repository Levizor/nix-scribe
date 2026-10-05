from dataclasses import dataclass
from functools import cached_property


@dataclass(frozen=True)
class DiscoveredPackage:
    name: str
    repository: str


@dataclass(frozen=True)
class ResolvedPackage:
    name: str
    original: DiscoveredPackage
    category: str | None = None

    @property
    def original_name(self) -> str:
        return self.original.name

    @property
    def repository(self) -> str:
        return self.original.repository


class PackageState:
    def __init__(
        self,
        packages: list[ResolvedPackage],
        unmapped: list[str] | None = None,
    ) -> None:
        self._packages = packages
        self._unmapped = sorted(unmapped or [])
        self._claimed: set[str] = set()

    @property
    def resolved(self) -> list[ResolvedPackage]:
        """All resolved packages discovered on the system."""
        return self._packages

    @property
    def packages(self) -> list[ResolvedPackage]:
        """Alias for resolved packages."""
        return self._packages

    @property
    def unmapped(self) -> list[str]:
        """Native package names that could not be mapped to Nixpkgs."""
        return self._unmapped

    @property
    def claimed(self) -> set[str]:
        """Set of package attribute names claimed by specialized modules."""
        return self._claimed

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

    def claim(self, attribute_name: str) -> bool:
        """Claims a package if present so it won't be emitted in systemPackages.

        Returns True if the package was present and claimed, False otherwise.
        """
        if self.has(attribute_name):
            self._claimed.add(attribute_name)
            return True
        return False

    def is_claimed(self, attribute_name: str) -> bool:
        return attribute_name in self._claimed

    def get_by_category(self, category: str) -> list[ResolvedPackage]:
        """Queries resolved packages by their upstream category."""
        return [pkg for pkg in self._packages if pkg.category == category]

    def get_unclaimed(self) -> list[ResolvedPackage]:
        """Alias for unclaimed property."""
        return self.unclaimed

    @classmethod
    def empty(cls) -> "PackageState":
        return cls(packages=[], unmapped=[])
