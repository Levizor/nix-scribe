from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class Gdm(NixModule, prefix="services.displayManager.gdm", claims={"gdm"}):
    """Gnome display manager"""

    enable: bool = option()
    wayland: bool = option()
    autoLogin_delay: int = option("autoLogin.delay")
    debug: bool = option()
    settings: dict[str, Any] = option()
