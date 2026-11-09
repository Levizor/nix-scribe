from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class CosmicGreeter(
    NixModule,
    prefix="services.displayManager.cosmic-greeter",
    claims={"cosmic-greeter"},
):
    """cosmic-greeter displayManager"""

    enable: bool = option(default=False)
