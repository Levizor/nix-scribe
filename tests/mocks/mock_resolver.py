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
                    repo, pkg_name = key
                    self.add_mapping(pkg_name, target, repository=repo)
                else:
                    self.add_mapping(key, target)

    def add_mapping(
        self,
        package_name: str,
        target: str | ResolvedPackage | None,
        repository: str | None = None,
        category: str | None = None,
    ) -> None:
        key: str | tuple[str, str] = (
            (repository, package_name) if repository is not None else package_name
        )
        self._mapping[key] = (target, category)

    def resolve(self, package: DiscoveredPackage) -> ResolvedPackage | None:
        val = self._mapping.get(
            (package.repository, package.name), self._mapping.get(package.name)
        )
        if val is None:
            return None
        target, category = val
        if target is None:
            return None
        if isinstance(target, ResolvedPackage):
            return target
        return ResolvedPackage(
            name=target,
            original=package,
            category=category,
        )
