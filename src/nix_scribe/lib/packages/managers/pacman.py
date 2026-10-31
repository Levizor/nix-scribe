from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from nix_scribe.lib.packages.manager import PackageManager, register_package_manager
from nix_scribe.lib.packages.models import DiscoveredPackage, InstallReason
from nix_scribe.lib.parsers.pacman import parse_pacman_desc

if TYPE_CHECKING:
    from nix_scribe.lib.context import SystemContext

logger = logging.getLogger(__name__)

PACMAN_LOCAL_DIR = "/var/lib/pacman/local"
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

    def discover_packages(self, context: SystemContext) -> list[DiscoveredPackage]:
        """Discovers installed packages by scanning /var/lib/pacman/local/*/desc."""
        if not self.detect(context):
            return []

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
            if reason_raw == "1" or name in ARCH_BASE_PACKAGES:
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
