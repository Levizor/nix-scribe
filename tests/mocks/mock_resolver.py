from nix_scribe.lib.packages import (
    DiscoveredPackage,
    PackageResolver,
    ResolvedPackage,
)


class MockPackageResolver(PackageResolver):
    def __init__(
        self,
        mapping: dict[str, str | ResolvedPackage | None]
        | dict[tuple[str, str], str | ResolvedPackage | None]
        | None = None,
    ) -> None:
        self._mapping: dict[str | tuple[str, str], ResolvedPackage | None] = {}
        if mapping:
            for key, target in mapping.items():
                if isinstance(key, tuple):
                    distro, pkg_name = key
                    self.add_mapping(pkg_name, target, distro=distro)
                else:
                    self.add_mapping(key, target)

    def add_mapping(
        self,
        package_name: str,
        target: str | ResolvedPackage | None,
        distro: str | None = None,
        repository: str | None = None,
        category: str | None = None,
    ) -> None:
        if isinstance(target, ResolvedPackage):
            resolved = target
        elif isinstance(target, str):
            resolved = ResolvedPackage(
                name=target,
                original_name=package_name,
                repository=repository or distro,
                category=category,
            )
        else:
            resolved = None

        if distro is not None:
            self._mapping[(distro, package_name)] = resolved
        else:
            self._mapping[package_name] = resolved

    def resolve(self, package: DiscoveredPackage) -> ResolvedPackage | None:
        if (package.distro, package.name) in self._mapping:
            return self._mapping[(package.distro, package.name)]
        return self._mapping.get(package.name)
