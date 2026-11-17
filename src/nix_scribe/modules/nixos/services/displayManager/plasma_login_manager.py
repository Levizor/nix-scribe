from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class PlasmaLoginManager(
    NixModule,
    prefix="services.displayManager.plasma-login-manager",
    claims={"kdePackages.plasma-login-manager"},
):
    """Plasma Login Manager (Greeter)"""

    enable: bool = option()
    settings: dict[str, Any] = option()
