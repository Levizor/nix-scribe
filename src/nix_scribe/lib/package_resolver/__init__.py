from nix_scribe.lib.package_resolver.base import PackageResolver
from nix_scribe.lib.package_resolver.models import ResolvedPackage
from nix_scribe.lib.package_resolver.provider import (
    get_package_resolver,
    set_package_resolver,
)

__all__ = [
    "PackageResolver",
    "ResolvedPackage",
    "get_package_resolver",
    "set_package_resolver",
]
