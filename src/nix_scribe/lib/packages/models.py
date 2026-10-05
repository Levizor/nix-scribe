from dataclasses import dataclass
from functools import cached_property


@dataclass(frozen=True)
class DiscoveredPackage:
    name: str
    distro: str


@dataclass(frozen=True)
class ResolvedPackage:
    name: str
    original_name: str
    repository: str | None = None
    category: str | None = None


class PackageState:
    def __init__(
        self,
        packages: list[ResolvedPackage],
        unmapped: list[str] | None = None,
    ) -> None:
        self.packages = packages
        self.unmapped = sorted(unmapped or [])
        self.claimed: set[str] = set()

    @cached_property
    def by_attribute(self) -> dict[str, ResolvedPackage]:
        return {pkg.name: pkg for pkg in self.packages}

    def has(self, attribute_name: str) -> bool:
        """Module API: check if a package exists on the system."""
        return attribute_name in self.by_attribute

    def claim(self, attribute_name: str) -> bool:
        """Claims a package if present so it won't be emitted in systemPackages.

        Returns True if the package was present and claimed, False otherwise.
        """
        if self.has(attribute_name):
            self.claimed.add(attribute_name)
            return True
        return False

    def is_claimed(self, attribute_name: str) -> bool:
        return attribute_name in self.claimed

    def get_by_category(self, category: str) -> list[ResolvedPackage]:
        """Queries resolved packages by their upstream category."""
        return [pkg for pkg in self.packages if pkg.category == category]

    def get_unclaimed(self) -> list[ResolvedPackage]:
        """Returns all resolved packages not claimed by any specialized module."""
        return [
            pkg for attr, pkg in self.by_attribute.items() if attr not in self.claimed
        ]

    @classmethod
    def empty(cls) -> "PackageState":
        return cls(packages=[], unmapped=[])
