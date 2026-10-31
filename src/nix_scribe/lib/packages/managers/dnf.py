from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from nix_scribe.lib.packages.manager import PackageManager, register_package_manager
from nix_scribe.lib.packages.models import DiscoveredPackage, InstallReason
from nix_scribe.lib.parsers.kv import parse_kv

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext

logger = logging.getLogger(__name__)

RPMDB_SQLITE_PATHS = [
    "/var/lib/rpm/rpmdb.sqlite",
    "/usr/lib/sysimage/rpm/rpmdb.sqlite",
]
DNF_HISTORY_PATHS = [
    "/var/lib/dnf/history.sqlite",
    "/usr/lib/sysimage/libdnf5/transaction_history.sqlite",
]
OS_RELEASE_PATHS = [
    "/etc/os-release",
    "/usr/lib/os-release",
]

PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+._-]*$")

USER_REASONS = {2, 5, 6}
ACTION_REMOVE = 8

FEDORA_BASE_PACKAGES = {
    "basesystem",
    "fedora-release",
    "fedora-release-common",
    "fedora-repos",
    "filesystem",
    "setup",
    "glibc",
    "glibc-common",
    "kernel",
    "kernel-core",
    "kernel-modules",
    "kernel-modules-core",
    "systemd",
    "systemd-libs",
    "systemd-udev",
    "dnf",
    "dnf5",
    "rpm",
    "coreutils",
    "coreutils-common",
    "bash",
    "shadow-utils",
}


class DnfManager(PackageManager):
    name = "dnf"
    distro = "fedora"

    def detect(self, context: SystemContext) -> bool:
        """Returns True if RPM SQLite database or DNF state directory exists."""
        return any(
            context.path_exists(p) for p in RPMDB_SQLITE_PATHS
        ) or context.path_exists("/var/lib/dnf")

    def _detect_repository(self, context: SystemContext) -> str:
        """Detects Fedora version from os-release to match pkgmap repository namespace."""
        for path in OS_RELEASE_PATHS:
            if context.path_exists(path):
                try:
                    data = parse_kv(context.read_file(path))
                    os_id = data.get("ID", "").lower()
                    id_like = data.get("ID_LIKE", "").lower()
                    if os_id == "fedora" or "fedora" in id_like:
                        version = data.get("VERSION_ID", "").strip()
                        if version.isdigit():
                            return f"fedora_{version}"
                        return "fedora_41"
                except Exception:
                    pass
        return "fedora_41"

    def _query_rpmdb_packages(self, context: SystemContext, path: str) -> list[str]:
        """Queries installed package names from rpmdb.sqlite via context.open_sqlite."""
        try:
            with context.open_sqlite(path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='Name'"
                )
                if not cursor.fetchone():
                    return []
                cursor.execute("SELECT DISTINCT key FROM Name WHERE key IS NOT NULL")
                rows = cursor.fetchall()
                return sorted([str(r[0]).strip() for r in rows if r[0]])
        except Exception as e:
            logger.warning(f"Failed to read RPM database at {path}: {e}")
            return []

    def _query_dnf_history(
        self, context: SystemContext, path: str
    ) -> dict[str, InstallReason]:
        """Queries transaction history from DNF history.sqlite and resolves reasons."""
        try:
            with context.open_sqlite(path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trans', 'trans_item', 'rpm')"
                )
                found_tables = {r[0] for r in cursor.fetchall()}
                if not {"trans", "trans_item", "rpm"}.issubset(found_tables):
                    return {}

                cursor.execute(
                    """
                    SELECT r.name, ti.action, ti.reason
                    FROM trans_item ti
                    JOIN rpm r ON ti.item_id = r.id
                    JOIN trans t ON ti.trans_id = t.id
                    ORDER BY ti.trans_id ASC, ti.id ASC
                    """
                )
                rows = cursor.fetchall()

                history_map: dict[str, InstallReason] = {}
                for name, action, reason in rows:
                    if not name:
                        continue
                    pkg_name = str(name).strip()
                    if int(action) == ACTION_REMOVE:
                        history_map.pop(pkg_name, None)
                    elif int(reason) in USER_REASONS:
                        history_map[pkg_name] = InstallReason.EXPLICIT
                    else:
                        history_map[pkg_name] = InstallReason.DEPENDENCY
                return history_map
        except Exception as e:
            logger.warning(f"Failed to read DNF history at {path}: {e}")
            return {}

    def _classify_packages(
        self,
        installed_names: list[str],
        history_map: dict[str, InstallReason] | None,
    ) -> dict[str, InstallReason]:
        """Classifies installed packages into explicit, preinstalled, or dependency tiers."""
        classified: dict[str, InstallReason] = {}
        for name in installed_names:
            if not PACKAGE_NAME_PATTERN.match(name):
                continue

            if name in FEDORA_BASE_PACKAGES:
                classified[name] = InstallReason.DEPENDENCY
            elif history_map is not None and name in history_map:
                classified[name] = history_map[name]
            elif history_map is not None:
                classified[name] = InstallReason.PREINSTALLED
            else:
                classified[name] = InstallReason.EXPLICIT

        return classified

    def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
        """Discovers installed packages by querying RPM database and DNF transaction history."""
        rpmdb_path = next(
            (p for p in RPMDB_SQLITE_PATHS if context.path_exists(p)), None
        )
        if not rpmdb_path:
            return []

        installed_names = self._query_rpmdb_packages(context, rpmdb_path)

        history_path = next(
            (p for p in DNF_HISTORY_PATHS if context.path_exists(p)), None
        )
        history_map = (
            self._query_dnf_history(context, history_path) if history_path else None
        )

        classified = self._classify_packages(installed_names, history_map)
        repository = self._detect_repository(context)

        return [
            DiscoveredPackage(name=name, repository=repository, reason=reason)
            for name, reason in sorted(classified.items())
        ]


register_package_manager(DnfManager)
