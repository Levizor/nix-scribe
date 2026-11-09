from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Rtkit(NixModule, prefix="security.rtkit", claims={"rtkit"}):
    """RealtimeKit system service"""

    enable: bool = option(default=False)
    args: list[str] = option(default=[])
