from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class Sddm(
    NixModule,
    prefix="services.displayManager.sddm",
    claims={"kdePackages.sddm", "kdePackages.sddm-unwrapped"},
):
    """Simple Desktop Display Manager"""

    enable: bool = option()
    wayland_enable: bool = option("wayland.enable")
    autoNumlock: bool = option()
    theme: str = option()
    settings: dict[str, Any] = option()
