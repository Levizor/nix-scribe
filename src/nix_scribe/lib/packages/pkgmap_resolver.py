from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import pkgmap

from nix_scribe.lib.packages.models import DiscoveredPackage, ResolvedPackage
from nix_scribe.lib.packages.resolver import PackageResolver


class PkgmapPackageResolver(PackageResolver):
    """Package resolver powered by the pkgmap cross-distribution resolution library."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else None

    def resolve(self, package: DiscoveredPackage) -> ResolvedPackage | None:
        """Resolves a single DiscoveredPackage into a ResolvedPackage using pkgmap."""
        match = pkgmap.resolve(
            package=package.name,
            from_repo=package.repository,
            to_repo="nixpkgs",
            db_path=self.db_path,
        )
        if match is None:
            return None
        return ResolvedPackage(name=match.name, original=package)

    def resolve_many(
        self, packages: list[DiscoveredPackage]
    ) -> tuple[list[ResolvedPackage], list[DiscoveredPackage]]:
        """Resolves a list of DiscoveredPackage instances using batch queries grouped by repository."""
        if not packages:
            return [], []

        by_repo: dict[str, list[DiscoveredPackage]] = defaultdict(list)
        for pkg in packages:
            by_repo[pkg.repository].append(pkg)

        match_map: dict[tuple[str, str], pkgmap.PackageResolution | None] = {}
        for repo, repo_pkgs in by_repo.items():
            names = [p.name for p in repo_pkgs]
            results = pkgmap.resolve_batch(
                packages=names,
                from_repo=repo,
                to_repo="nixpkgs",
                db_path=self.db_path,
            )
            for pkg_name, res in results.items():
                match_map[(repo, pkg_name)] = res

        resolved: list[ResolvedPackage] = []
        unmapped: list[DiscoveredPackage] = []

        for pkg in packages:
            match = match_map.get((pkg.repository, pkg.name))
            if match is not None:
                resolved.append(ResolvedPackage(name=match.name, original=pkg))
            else:
                unmapped.append(pkg)

        return resolved, unmapped
