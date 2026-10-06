from __future__ import annotations

from typing import TYPE_CHECKING

from nix_scribe.lib.packages.manager import PackageManager, register_package_manager
from nix_scribe.lib.packages.models import DiscoveredPackage, InstallReason
from nix_scribe.lib.parsers.apt import (
    parse_dpkg_status,
    parse_extended_states,
)
from nix_scribe.lib.parsers.kv import parse_kv

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext

DPKG_STATUS_PATH = "/var/lib/dpkg/status"
APT_EXTENDED_STATES_PATH = "/var/lib/apt/extended_states"
OS_RELEASE_PATHS = ["/etc/os-release", "/usr/lib/os-release"]

# Sections for internal binary plumbing, compilation headers, or kernel artifacts.
# User-facing applications and utilities reside in admin, devel, editors, net, utils, web, etc.
EXCLUDED_DEP_SECTIONS = {
    # GObject Introspection typelibs (gir1.2-*); internal runtime bindings.
    "introspection",
    # Operating system kernel images and modules; managed via boot.kernelPackages.
    "kernel",
    # C/C++ library headers and static libraries (*-dev); compilation artifacts.
    "libdevel",
    # Shared dynamic libraries; Nix packages bundle their own runtime closures.
    "libs",
    # Meta packages (ubuntu-desktop, task-*); NixOS defines system roles natively.
    "metapackages",
    # Obsolete or transitional shared libraries retained for backward compatibility.
    "oldlibs",
}

# Essential Unix base packages (e.g. coreutils, systemd, apt) handled natively by NixOS.
BASE_PRIORITIES = {
    "important",
    "required",
}


class AptManager(PackageManager):
    name = "apt"

    def detect(self, context: SystemContext) -> bool:
        """Returns True if dpkg status file exists on the target root."""
        return context.path_exists(DPKG_STATUS_PATH)

    def _detect_repository(self, context: SystemContext) -> str:
        """Determines whether the target Debian derivative is Ubuntu or standard Debian."""
        for path in OS_RELEASE_PATHS:
            if context.path_exists(path):
                try:
                    data = parse_kv(context.read_file(path))
                    os_id = data.get("ID", "").lower()
                    id_like = data.get("ID_LIKE", "").lower()
                    if os_id == "ubuntu" or "ubuntu" in id_like:
                        return "ubuntu"
                except Exception:
                    pass
        return "debian"

    def _classify_packages(
        self,
        status_records: dict[str, dict[str, str]],
        extended_records: dict[str, dict[str, str]],
    ) -> dict[str, InstallReason]:
        """Classifies installed packages into explicit, preinstalled, or dependency tiers.

        Explicit packages have Auto-Installed: 0 and are not essential Unix primitives.
        Preinstalled packages are non-library utilities that are not essential or base plumbing.
        Remaining installed packages are classified as dependencies.
        """
        installed_status: dict[str, dict[str, str]] = {
            name: status
            for name, status in status_records.items()
            if status.get("Status") == "install ok installed"
        }

        classified: dict[str, InstallReason] = {}
        for name, status in installed_status.items():
            is_base = (
                status.get("Essential") == "yes"
                or status.get("Priority") in BASE_PRIORITIES
            )
            section = status.get("Section", "").lower()
            is_excluded_section = section in EXCLUDED_DEP_SECTIONS
            auto_installed = extended_records.get(name, {}).get("Auto-Installed")

            if auto_installed == "0" and not is_base:
                classified[name] = InstallReason.EXPLICIT
            elif not is_base and not is_excluded_section:
                classified[name] = InstallReason.PREINSTALLED
            else:
                classified[name] = InstallReason.DEPENDENCY

        return classified

    def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
        """Parses extended_states and dpkg status to discover all installed packages with install reasons."""
        if not context.path_exists(DPKG_STATUS_PATH):
            return []

        status_records = parse_dpkg_status(context.read_file(DPKG_STATUS_PATH))

        extended_records: dict[str, dict[str, str]] = {}
        if context.path_exists(APT_EXTENDED_STATES_PATH):
            extended_records = parse_extended_states(
                context.read_file(APT_EXTENDED_STATES_PATH)
            )

        classified = self._classify_packages(
            status_records=status_records,
            extended_records=extended_records,
        )

        repository = self._detect_repository(context)
        return [
            DiscoveredPackage(name=pkg_name, repository=repository, reason=reason)
            for pkg_name, reason in sorted(classified.items())
        ]


register_package_manager(AptManager)
