from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Vim(NixModule, prefix="programs.vim", claims={"vim"}):
    """Enable vim editor"""

    enable: bool = option()
    defaultEditor: bool = option()
