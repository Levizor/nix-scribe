from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class SystemPackages(NixModule, prefix="environment"):
    """System-wide packages"""

    systemPackages: Any = option(
        default=None,
        arguments={"pkgs"},
        comment="See packages.log for the full package mapping report and unmapped packages.",
    )
