import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import comment, nix_with, raw
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.packages.models import (
    DiscoveredPackage,
    PackageState,
    ResolvedPackage,
)
from nix_scribe.lib.registry import Module, ModulePhase

logger = logging.getLogger(__name__)

system_packages = Module("environment.system_packages", phase=ModulePhase.LATE)

STANDARD_REPOSITORIES = {
    "alpine",
    "arch",
    "debian",
    "fedora",
    "ubuntu",
}


def _format_package_item(pkg: ResolvedPackage) -> raw:
    """Formats a resolved package into an expressive Nix package item with provenance comments."""
    if pkg.name != pkg.original_name:
        return raw(f"{pkg.name} /* from {pkg.repository}:{pkg.original_name} */")
    if pkg.repository and pkg.repository not in STANDARD_REPOSITORIES:
        return raw(f"{pkg.name} /* from {pkg.repository} */")
    return raw(pkg.name)


def _format_unmapped_item(pkg: DiscoveredPackage) -> comment:
    """Formats an unmapped discovered package with repository details."""
    if pkg.repository:
        return comment(f"unmapped: {pkg.name} (repo: {pkg.repository})")
    return comment(f"unmapped: {pkg.name}")


@system_packages.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {
        "packages": context.packages,
    }


@system_packages.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir or not ir.get("packages"):
        return None

    state: PackageState = ir["packages"]
    packages = state.unclaimed
    unmapped = [p for p in state.unmapped if not p.is_dependency]

    explicit = sorted([p for p in packages if p.is_explicit], key=lambda p: p.name)
    preinstalled = sorted(
        [p for p in packages if p.is_preinstalled], key=lambda p: p.name
    )

    if not explicit and not preinstalled and not unmapped:
        return None

    items: list[raw] = []

    if explicit:
        if preinstalled:
            items.append(comment("User-installed packages"))
        for pkg in explicit:
            items.append(_format_package_item(pkg))

    if preinstalled:
        prefix = "\n" if explicit else ""
        items.append(comment(f"{prefix}Pre-installed distribution utilities"))
        for pkg in preinstalled:
            items.append(_format_package_item(pkg))

    for pkg in sorted(unmapped, key=lambda p: p.name):
        items.append(_format_unmapped_item(pkg))

    return ConfigFragment(
        name="system-packages",
        description="System-wide packages",
        data={"environment.systemPackages": nix_with("pkgs", items)},
    )
