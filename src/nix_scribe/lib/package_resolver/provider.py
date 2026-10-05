from nix_scribe.lib.package_resolver.base import PackageResolver

_current_resolver: PackageResolver | None = None


def get_package_resolver(distro: str | None = None) -> PackageResolver:
    """Returns the globally configured package resolver."""
    global _current_resolver
    if _current_resolver is None:
        try:
            from nix_scribe.lib.package_resolver.sqlite import SqlitePackageResolver

            _current_resolver = SqlitePackageResolver(distro=distro)
        except (ImportError, Exception):
            pass

    if _current_resolver is None:
        raise RuntimeError(
            "No package resolver configured. Provide one using set_package_resolver() "
            "or ensure package_map.sqlite is available."
        )
    return _current_resolver


def set_package_resolver(resolver: PackageResolver | None) -> None:
    """Sets or resets the global package resolver instance."""
    global _current_resolver
    _current_resolver = resolver
