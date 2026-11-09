from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Hyprland(NixModule, prefix="programs.hyprland", claims={"hyprland"}):
    """Hyprland compositor"""

    enable: bool = option(default=False)
