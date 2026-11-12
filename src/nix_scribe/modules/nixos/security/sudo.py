from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Sudo(NixModule, prefix="security.sudo", claims={"sudo"}):
    """Sudo Configuration"""

    enable: bool = option(default=True)
    execWheelOnly: bool = option()
    wheelNeedsPassword: bool = option(default=True)
    keepTerminfo: bool = option(default=True)
    extraConfig: str = option()
