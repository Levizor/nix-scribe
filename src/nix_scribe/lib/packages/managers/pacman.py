from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from nix_scribe.lib.packages.manager import PackageManager, register_package_manager
from nix_scribe.lib.packages.models import DiscoveredPackage, InstallReason
from nix_scribe.lib.parsers.pacman import parse_pacman_desc
from nix_scribe.lib.parsers.pacman_log import (
    parse_pacman_cmdline,
    parse_pacman_log_cmdlines,
)

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext

logger = logging.getLogger(__name__)

PACMAN_LOCAL_DIR = "/var/lib/pacman/local"
PACMAN_LOG_PATHS = ["/var/log/pacman.log.1", "/var/log/pacman.log"]
PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9@._+-]*$")

ARCH_BASE_PACKAGES = {
    "base",
    "base-devel",
}


class PacmanManager(PackageManager):
    name = "pacman"
    distro = "arch"

    def detect(self, context: SystemContext) -> bool:
        """Returns True if pacman local database directory exists on the target root."""
        return context.path_exists(PACMAN_LOCAL_DIR)

    def _read_history_explicit_packages(
        self, context: SystemContext
    ) -> set[str] | None:
        log_found = False
        explicit: set[str] = set()
        for path in PACMAN_LOG_PATHS:
            if context.path_exists(path):
                log_found = True
                try:
                    content = context.read_file(path)
                    for _, cmdline in parse_pacman_log_cmdlines(content):
                        action, pkgs = parse_pacman_cmdline(cmdline)
                        if action == "install":
                            explicit.update(pkgs)
                        elif action in ("remove", "asdeps"):
                            explicit.difference_update(pkgs)
                except Exception as e:
                    logger.warning(f"Failed to read pacman log at {path}: {e}")
        return explicit if log_found else None

    def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
        """Discovers installed packages by scanning /var/lib/pacman/local/*/desc."""
        if not self.detect(context):
            return []

        explicit_from_history = self._read_history_explicit_packages(context)
        entries = context.list_directory(PACMAN_LOCAL_DIR)
        packages: list[DiscoveredPackage] = []

        for entry in sorted(entries):
            desc_path = f"{PACMAN_LOCAL_DIR}/{entry}/desc"
            if not context.path_exists(desc_path):
                continue

            try:
                content = context.read_file(desc_path)
                data = parse_pacman_desc(content)
            except Exception as e:
                logger.warning(f"Failed to read pacman desc for {entry}: {e}")
                continue

            name = data.get("NAME")
            if not name or not isinstance(name, str):
                continue

            name = name.strip()
            if not PACKAGE_NAME_PATTERN.match(name):
                continue

            reason_raw = str(data.get("REASON", "0")).strip()
            if name in ARCH_BASE_PACKAGES:
                reason = InstallReason.DEPENDENCY
            elif explicit_from_history is not None:
                if name in explicit_from_history:
                    reason = InstallReason.EXPLICIT
                elif reason_raw == "0":
                    reason = InstallReason.PREINSTALLED
                else:
                    reason = InstallReason.DEPENDENCY
            else:
                if reason_raw == "1":
                    reason = InstallReason.DEPENDENCY
                else:
                    reason = InstallReason.EXPLICIT

            packages.append(
                DiscoveredPackage(
                    name=name,
                    repository="arch",
                    reason=reason,
                )
            )

        return packages


register_package_manager(PacmanManager)
