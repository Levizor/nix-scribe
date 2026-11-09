import logging
from typing import Any

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import combination, comment, nix_with, raw
from nix_scribe.lib.packages.models import (
    DiscoveredPackage,
    PackageState,
    ResolvedPackage,
)
from nix_scribe.lib.registry import ModulePhase, Scanner
from nix_scribe.modules.nixos.environment.system_packages import SystemPackages

logger = logging.getLogger(__name__)

system_packages = Scanner(
    "environment.system_packages",
    phase=ModulePhase.LATE,
    description="System-wide packages",
)


def _format_package_item(
    pkg: ResolvedPackage | DiscoveredPackage,
) -> combination:
    """Formats a package into an expressive Nix package item with provenance comments."""
    orig_name = getattr(pkg, "original_name", pkg.name)
    repo = pkg.repository or ""
    provenance = f"{repo}:{orig_name}" if repo else orig_name
    return combination([raw(pkg.name), comment(f" from {provenance}")])


def _build_packages_report(
    explicit: list[ResolvedPackage],
    preinstalled: list[ResolvedPackage],
    claimed: list[ResolvedPackage],
    dependencies: list[ResolvedPackage],
    unmapped: list[DiscoveredPackage],
    state: PackageState | None = None,
) -> str:
    def format_claimed(p: ResolvedPackage) -> str:
        base = _format_package_item(p)
        if state:
            by = state.claimed_by(p.name)
            if by:
                return f"{base} (claimed by {by})"
        return str(base)

    sections = [
        ("User-installed packages:", [_format_package_item(p) for p in explicit]),
        (
            "Pre-installed distribution utilities:",
            [_format_package_item(p) for p in preinstalled],
        ),
        ("Claimed packages:", [format_claimed(p) for p in claimed]),
        ("Excluded dependencies:", [_format_package_item(p) for p in dependencies]),
        ("Unmapped packages:", [_format_package_item(p) for p in unmapped]),
    ]
    report = ["# Package Mapping Report"]
    for title, items in sections:
        if items:
            report.append(f"{title}\n" + "\n".join(f"  {item}" for item in items))
    return "\n\n".join(report) + "\n"


@system_packages.scanner()
def scan(context: SystemContext) -> SystemPackages | None:
    state: PackageState = context.packages
    if not state.resolved and not state.unmapped:
        return None

    packages = state.unclaimed
    explicit = sorted([p for p in packages if p.is_explicit], key=lambda p: p.name)
    preinstalled = sorted(
        [p for p in packages if p.is_preinstalled], key=lambda p: p.name
    )
    claimed = sorted(
        [
            state.by_attribute[attr]
            for attr in state.claimed
            if attr in state.by_attribute
        ],
        key=lambda p: p.name,
    )
    dependencies = sorted(
        [p for p in state.packages if p.is_dependency],
        key=lambda p: (p.name, p.original_name),
    )
    unmapped = sorted(state.unmapped, key=lambda p: (p.repository, p.name))

    if not explicit and not preinstalled and not unmapped and not claimed:
        return None

    report = _build_packages_report(
        explicit=explicit,
        preinstalled=preinstalled,
        claimed=claimed,
        dependencies=dependencies,
        unmapped=unmapped,
        state=state,
    )

    items: list[Any] = []

    if explicit:
        if preinstalled:
            items.append(comment("User-installed packages"))
        for pkg in explicit:
            items.append(_format_package_item(pkg))

    if preinstalled:
        prefix = "\n" if explicit else ""
        items.append(
            comment(
                f"{prefix}Pre-installed distribution utilities (commented out by default)"
            )
        )
        for pkg in preinstalled:
            items.append(comment(str(_format_package_item(pkg))))

    mod = SystemPackages()
    mod.add_asset(Asset("packages.log", report))

    if items:
        mod.systemPackages = nix_with("pkgs", items)

    return mod
