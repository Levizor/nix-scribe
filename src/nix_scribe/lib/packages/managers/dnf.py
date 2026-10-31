from __future__ import annotations

import logging
import re
import shlex
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


def _is_bootstrap_cmdline(cmdline: str) -> bool:
    cmd_lower = cmdline.lower()
    return any(flag in cmd_lower for flag in ("--installroot", "anaconda", "kiwi"))


def _parse_dnf_cmdline(cmdline: str) -> tuple[str | None, set[str]]:
    try:
        tokens = shlex.split(cmdline)
    except Exception:
        tokens = cmdline.split()

    subcommand = None
    target_tokens: list[str] = []
    install_cmds = {"install", "reinstall", "in"}
    remove_cmds = {"remove", "erase", "rm"}

    for i, tok in enumerate(tokens):
        if tok in install_cmds:
            subcommand = "install"
            target_tokens = tokens[i + 1 :]
            break
        elif tok in remove_cmds:
            subcommand = "remove"
            target_tokens = tokens[i + 1 :]
            break

    packages: set[str] = set()
    if subcommand:
        skip_next = False
        for tok in target_tokens:
            if skip_next:
                skip_next = False
                continue
            if tok.startswith("-"):
                if tok in ("-c", "--config", "--releasever", "--setopt"):
                    skip_next = True
                continue
            clean_tok = (
                tok.rsplit(".", 1)[0]
                if "." in tok
                and tok.rsplit(".", 1)[1] in ("x86_64", "noarch", "i686", "aarch64")
                else tok
            )
            if PACKAGE_NAME_PATTERN.match(clean_tok):
                packages.add(clean_tok)
            elif PACKAGE_NAME_PATTERN.match(tok):
                packages.add(tok)

    return subcommand, packages


class DnfManager(PackageManager):
    name = "dnf"
    distro = "fedora"

    def detect(self, context: SystemContext) -> bool:
        """Returns True if RPM SQLite database or DNF state directory exists."""
        return any(
            context.path_exists(p) for p in RPMDB_SQLITE_PATHS
        ) or context.path_exists("/var/lib/dnf")

    def _detect_repository(self, context: SystemContext) -> str:
        """Detects distribution from os-release to match pkgmap repository namespace."""
        # Defaults to the 'fedora' alias in pkgmap. Can be extended for other
        # DNF-based derivatives (e.g. centos, almalinux, rocky) in the future.
        for path in OS_RELEASE_PATHS:
            if context.path_exists(path):
                try:
                    data = parse_kv(context.read_file(path))
                    os_id = data.get("ID", "").lower()
                    id_like = data.get("ID_LIKE", "").lower()
                    if os_id == "fedora" or "fedora" in id_like:
                        return "fedora"
                except Exception:
                    pass
        return "fedora"

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
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trans', 'trans_item', 'rpm', 'pkg_name', 'trans_item_action', 'trans_item_reason', 'trans_cmdline')"
                )
                found_tables = {r[0] for r in cursor.fetchall()}
                if not {"trans", "trans_item", "rpm"}.issubset(found_tables):
                    return {}

                trans_cmdlines: dict[int, str] = {}
                if "pkg_name" in found_tables:
                    cursor.execute("PRAGMA table_info(trans)")
                    trans_cols = {r[1] for r in cursor.fetchall()}
                    if "description" in trans_cols:
                        cursor.execute(
                            "SELECT id, description FROM trans ORDER BY id ASC"
                        )
                        trans_cmdlines = {
                            r[0]: str(r[1] or "") for r in cursor.fetchall()
                        }
                    else:
                        cursor.execute("SELECT id FROM trans ORDER BY id ASC")
                        trans_cmdlines = {r[0]: "" for r in cursor.fetchall()}

                    user_reasons = USER_REASONS
                    if "trans_item_reason" in found_tables:
                        cursor.execute(
                            "SELECT id FROM trans_item_reason WHERE LOWER(name) IN ('user', 'group', 'external user')"
                        )
                        user_reasons = {r[0] for r in cursor.fetchall()} or USER_REASONS

                    remove_action = 5
                    if "trans_item_action" in found_tables:
                        cursor.execute(
                            "SELECT id FROM trans_item_action WHERE LOWER(name) = 'remove'"
                        )
                        row = cursor.fetchone()
                        if row:
                            remove_action = row[0]

                    cursor.execute(
                        """
                        SELECT pn.name, ti.action_id, ti.reason_id, ti.trans_id
                        FROM trans_item ti
                        JOIN rpm r ON ti.item_id = r.item_id
                        JOIN pkg_name pn ON r.name_id = pn.id
                        JOIN trans t ON ti.trans_id = t.id
                        ORDER BY ti.trans_id ASC, ti.id ASC
                        """
                    )
                else:
                    if "trans_cmdline" in found_tables:
                        cursor.execute(
                            "SELECT trans_id, cmdline FROM trans_cmdline ORDER BY trans_id ASC"
                        )
                        trans_cmdlines = {
                            r[0]: str(r[1] or "") for r in cursor.fetchall()
                        }

                    user_reasons = USER_REASONS
                    remove_action = ACTION_REMOVE
                    cursor.execute(
                        """
                        SELECT r.name, ti.action, ti.reason, ti.trans_id
                        FROM trans_item ti
                        JOIN rpm r ON ti.item_id = r.id
                        JOIN trans t ON ti.trans_id = t.id
                        ORDER BY ti.trans_id ASC, ti.id ASC
                        """
                    )

                rows = cursor.fetchall()

                items_by_trans: dict[int, list[tuple[str, int, int]]] = {}
                for name, action, reason, trans_id in rows:
                    if not name:
                        continue
                    items_by_trans.setdefault(trans_id, []).append(
                        (str(name).strip(), int(action), int(reason))
                    )

                all_trans_ids = sorted(
                    set(trans_cmdlines.keys()) | set(items_by_trans.keys())
                )
                history_map: dict[str, InstallReason] = {}

                for trans_id in all_trans_ids:
                    cmdline = trans_cmdlines.get(trans_id, "")
                    is_bootstrap = _is_bootstrap_cmdline(cmdline)

                    for pkg_name, action, reason in items_by_trans.get(trans_id, []):
                        if action == remove_action:
                            history_map.pop(pkg_name, None)
                        elif is_bootstrap:
                            if (
                                reason in user_reasons
                                and pkg_name not in FEDORA_BASE_PACKAGES
                            ):
                                history_map[pkg_name] = InstallReason.PREINSTALLED
                            else:
                                history_map[pkg_name] = InstallReason.DEPENDENCY
                        else:
                            if reason in user_reasons:
                                history_map[pkg_name] = InstallReason.EXPLICIT
                            else:
                                history_map[pkg_name] = InstallReason.DEPENDENCY

                    if not is_bootstrap and cmdline:
                        subcmd, cmd_pkgs = _parse_dnf_cmdline(cmdline)
                        if subcmd == "install":
                            for pkg in cmd_pkgs:
                                history_map[pkg] = InstallReason.EXPLICIT
                        elif subcmd == "remove":
                            for pkg in cmd_pkgs:
                                history_map.pop(pkg, None)

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
