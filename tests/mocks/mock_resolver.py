from nix_scribe.lib.package_resolver import PackageResolver, ResolvedPackage


class MockPackageResolver(PackageResolver):
    def __init__(
        self,
        mapping: dict[str, str | ResolvedPackage | None] | None = None,
        distro: str | None = None,
    ) -> None:
        super().__init__(distro=distro)
        self._mapping: dict[str, ResolvedPackage | None] = {}
        if mapping:
            for pkg_name, target in mapping.items():
                self.add_mapping(pkg_name, target)

    def add_mapping(
        self,
        package_name: str,
        target: str | ResolvedPackage | None,
        repository: str | None = None,
    ) -> None:
        if isinstance(target, ResolvedPackage):
            self._mapping[package_name] = target
        elif isinstance(target, str):
            self._mapping[package_name] = ResolvedPackage(
                name=target,
                original_name=package_name,
                repository=repository,
            )
        else:
            self._mapping[package_name] = None

    def resolve(self, package_name: str) -> ResolvedPackage | None:
        return self._mapping.get(package_name)
