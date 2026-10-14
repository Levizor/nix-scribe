from __future__ import annotations

import re
from typing import TYPE_CHECKING

from nix_scribe.lib.packages.manager import PackageManager, register_package_manager
from nix_scribe.lib.packages.models import DiscoveredPackage, InstallReason
from nix_scribe.lib.parsers.apt import (
    AptHistoryRecord,
    parse_apt_history,
    parse_dpkg_status,
    parse_extended_states,
)
from nix_scribe.lib.parsers.kv import parse_kv

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext

DPKG_STATUS_PATH = "/var/lib/dpkg/status"
APT_EXTENDED_STATES_PATH = "/var/lib/apt/extended_states"
APT_LOG_DIR = "/var/log/apt"
APT_HISTORY_LOG_PATH = "/var/log/apt/history.log"
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

PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+.-]+$")


def _history_file_sort_key(filename: str) -> int:
    if filename == "history.log":
        return 0
    parts = filename.rsplit(".", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return int(parts[1])
    return 9999


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

    @staticmethod
    def _extract_explicit_packages(records: list[AptHistoryRecord]) -> set[str]:
        explicit: set[str] = set()
        for record in records:
            for pkg in record.install:
                if "automatic" not in pkg.flags:
                    explicit.add(pkg.name)

            for pkg in record.remove:
                explicit.discard(pkg.name)

            for pkg in record.purge:
                explicit.discard(pkg.name)

            if record.commandline:
                manual_match = re.search(
                    r"\bapt-mark\s+(?:manual|unmarkauto)\s+([^;\n]+)",
                    record.commandline,
                )
                if manual_match:
                    for token in manual_match.group(1).split():
                        if not token.startswith("-"):
                            pkg_name = token.split(":", 1)[0]
                            if PACKAGE_NAME_PATTERN.match(pkg_name):
                                explicit.add(pkg_name)

                auto_match = re.search(
                    r"\bapt-mark\s+(?:auto|markauto)\s+([^;\n]+)",
                    record.commandline,
                )
                if auto_match:
                    for token in auto_match.group(1).split():
                        if not token.startswith("-"):
                            pkg_name = token.split(":", 1)[0]
                            explicit.discard(pkg_name)

        return explicit

    def _read_history_explicit_packages(self, context: SystemContext) -> set[str]:
        records: list[AptHistoryRecord] = []
        if context.path_exists(APT_LOG_DIR):
            try:
                entries = context.list_directory(APT_LOG_DIR)
                history_files = [
                    entry
                    for entry in entries
                    if entry.startswith("history.log")
                    and not entry.endswith((".gz", ".xz", ".bz2", ".zst", ".tmp"))
                ]
                history_files.sort(key=_history_file_sort_key, reverse=True)
                for filename in history_files:
                    path = f"{APT_LOG_DIR}/{filename}"
                    records.extend(parse_apt_history(context.read_file(path)))
            except Exception:
                pass
        elif context.path_exists(APT_HISTORY_LOG_PATH):
            try:
                records.extend(
                    parse_apt_history(context.read_file(APT_HISTORY_LOG_PATH))
                )
            except Exception:
                pass

        return self._extract_explicit_packages(records)

    def _classify_packages(
        self,
        status_records: dict[str, dict[str, str]],
        extended_records: dict[str, dict[str, str]],
        explicit_from_history: set[str] | None = None,
    ) -> dict[str, InstallReason]:
        """Classifies installed packages into explicit, preinstalled, or dependency tiers.

        Explicit packages have Auto-Installed: 0 or are recorded in apt history.log,
        and are not essential Unix primitives.
        Preinstalled packages are non-library utilities that are not essential or base plumbing.
        Remaining installed packages are classified as dependencies.
        """
        installed_status: dict[str, dict[str, str]] = {
            name: status
            for name, status in status_records.items()
            if status.get("Status") == "install ok installed"
        }

        history_explicit = explicit_from_history or set()
        classified: dict[str, InstallReason] = {}
        for name, status in installed_status.items():
            is_base = (
                status.get("Essential") == "yes"
                or status.get("Priority") in BASE_PRIORITIES
            )
            section = status.get("Section", "").lower()
            is_excluded_section = section in EXCLUDED_DEP_SECTIONS
            auto_installed = extended_records.get(name, {}).get("Auto-Installed")

            is_explicit = (auto_installed == "0") or (
                name in history_explicit and auto_installed != "1"
            )

            if is_explicit and not is_base:
                classified[name] = InstallReason.EXPLICIT
            elif not is_base and not is_excluded_section:
                classified[name] = InstallReason.PREINSTALLED
            else:
                classified[name] = InstallReason.DEPENDENCY

        return classified

    def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
        """Parses extended_states, dpkg status, and history logs to discover installed packages."""
        if not context.path_exists(DPKG_STATUS_PATH):
            return []

        status_records = parse_dpkg_status(context.read_file(DPKG_STATUS_PATH))

        extended_records: dict[str, dict[str, str]] = {}
        if context.path_exists(APT_EXTENDED_STATES_PATH):
            extended_records = parse_extended_states(
                context.read_file(APT_EXTENDED_STATES_PATH)
            )

        explicit_from_history = self._read_history_explicit_packages(context)

        classified = self._classify_packages(
            status_records=status_records,
            extended_records=extended_records,
            explicit_from_history=explicit_from_history,
        )

        repository = self._detect_repository(context)
        return [
            DiscoveredPackage(name=pkg_name, repository=repository, reason=reason)
            for pkg_name, reason in sorted(classified.items())
        ]


register_package_manager(AptManager)
