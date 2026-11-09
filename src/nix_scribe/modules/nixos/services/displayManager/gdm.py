from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class Gdm(NixModule, prefix="services.displayManager.gdm", claims={"gdm"}):
    """Gnome display manager"""

    enable: bool = option(default=False)
    wayland: bool | None = option(omit_default=False)
    autoLogin_delay: int | None = option("autoLogin.delay")
    debug: bool = option(default=False)
    settings: dict[str, Any] = option(default={})
