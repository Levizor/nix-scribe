from __future__ import annotations

from abc import ABC, abstractmethod

from nix_scribe.lib.packages.models import DiscoveredPackage, ResolvedPackage


class PackageResolver(ABC):
    @abstractmethod
    def resolve(self, package: DiscoveredPackage) -> ResolvedPackage | None:
        """Resolves a DiscoveredPackage into a canonical ResolvedPackage."""
        pass

    def resolve_many(
        self, packages: list[DiscoveredPackage]
    ) -> tuple[list[ResolvedPackage], list[str]]:
        """Resolves a list of DiscoveredPackage instances, returning resolved packages and unmapped names."""
        resolved: list[ResolvedPackage] = []
        unmapped: list[str] = []

        for pkg in packages:
            res = self.resolve(pkg)
            if res is not None:
                resolved.append(res)
            else:
                unmapped.append(pkg.name)

        return resolved, unmapped


class DummyPackageResolver(PackageResolver):
    """Dummy package resolver that passes every discovered package through as-is."""

    def resolve(self, package: DiscoveredPackage) -> ResolvedPackage | None:
        return ResolvedPackage(name=package.name, original=package)


_current_resolver: PackageResolver | None = None


def get_package_resolver() -> PackageResolver:
    """Returns the globally configured package resolver, defaulting to DummyPackageResolver."""
    global _current_resolver
    if _current_resolver is None:
        _current_resolver = DummyPackageResolver()
    return _current_resolver


def set_package_resolver(resolver: PackageResolver | None) -> None:
    """Sets or resets the global package resolver instance."""
    global _current_resolver
    _current_resolver = resolver
