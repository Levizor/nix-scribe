from abc import ABC, abstractmethod

from nix_scribe.lib.package_resolver.models import ResolvedPackage


class PackageResolver(ABC):
    def __init__(self, distro: str | None = None) -> None:
        self.distro = distro

    @abstractmethod
    def resolve(self, package_name: str) -> ResolvedPackage | None:
        """Resolves a native distro package name to a Nixpkgs attribute."""
        pass

    def resolve_many(
        self, package_names: list[str]
    ) -> tuple[list[ResolvedPackage], list[str]]:
        """Resolves a list of native package names, returning resolved packages and unmapped names."""
        resolved: list[ResolvedPackage] = []
        unmapped: list[str] = []

        for name in package_names:
            pkg = self.resolve(name)
            if pkg is not None:
                resolved.append(pkg)
            else:
                unmapped.append(name)

        return resolved, unmapped
