from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Nano(NixModule, prefix="programs.nano", claims={"nano"}):
    """nano editor"""

    enable: bool = option(default=False)
    nanorc: str = option(default="")
