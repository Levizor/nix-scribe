from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

import pkgmap

from nix_scribe.lib.packages.models import DiscoveredPackage, ResolvedPackage
from nix_scribe.lib.packages.resolver import PackageResolver

logger = logging.getLogger(__name__)

pkgmap.set_default_variant("core")


class PkgmapPackageResolver(PackageResolver):
    """Package resolver powered by the pkgmap cross-distribution resolution library."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        variant: pkgmap.DatabaseVariant = "core",
        fallback: bool = True,
    ) -> None:
        self.variant = variant
        pkgmap.set_default_variant(variant)
        self.db_path = Path(db_path) if db_path is not None else None
        self.fallback = fallback

    def resolve(self, package: DiscoveredPackage) -> ResolvedPackage | None:
        """Resolves a single DiscoveredPackage into a ResolvedPackage using pkgmap."""
        logger.debug(
            "Resolving package '%s' from repository '%s'",
            package.name,
            package.repository,
        )
        match = pkgmap.resolve(
            package=package.name,
            from_repo=package.repository,
            to_repo="nixpkgs",
            db_path=self.db_path,
            fallback=self.fallback,
        )
        if match is None:
            logger.debug(
                "Package '%s:%s' could not be resolved in nixpkgs",
                package.repository,
                package.name,
            )
            return None
        logger.debug(
            "Resolved '%s:%s' -> 'nixpkgs:%s'",
            package.repository,
            package.name,
            match.name,
        )
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

        logger.debug(
            "Batch resolving %d packages across %d repositories (%s) via pkgmap",
            len(packages),
            len(by_repo),
            ", ".join(sorted(by_repo.keys())),
        )

        match_map: dict[tuple[str, str], pkgmap.PackageResolution | None] = {}
        for repo, repo_pkgs in by_repo.items():
            names = [p.name for p in repo_pkgs]
            results = pkgmap.resolve_batch(
                packages=names,
                from_repo=repo,
                to_repo="nixpkgs",
                db_path=self.db_path,
                fallback=self.fallback,
            )
            for pkg_name, res in results.items():
                match_map[(repo, pkg_name)] = res
            logger.debug(
                "Batch resolved repository '%s': %d queries executed",
                repo,
                len(names),
            )

        resolved: list[ResolvedPackage] = []
        unmapped: list[DiscoveredPackage] = []

        for pkg in packages:
            match = match_map.get((pkg.repository, pkg.name))
            if match is not None:
                resolved.append(ResolvedPackage(name=match.name, original=pkg))
            else:
                unmapped.append(pkg)

        logger.debug(
            "Resolution completed: %d mapped to nixpkgs, %d unmapped",
            len(resolved),
            len(unmapped),
        )
        if unmapped:
            unmapped_sample = ", ".join(
                f"{p.repository}:{p.name}" for p in unmapped[:10]
            )
            if len(unmapped) > 10:
                unmapped_sample += f", ... (+{len(unmapped) - 10} more)"
            logger.debug("Unmapped packages sample: %s", unmapped_sample)

        return resolved, unmapped
