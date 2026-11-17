from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.displayManager.cosmic_greeter import (
    CosmicGreeter,
)

cosmic_greeter = Scanner("services.displayManager.cosmic-greeter")


@cosmic_greeter.scanner()
def scan(context: SystemContext) -> CosmicGreeter | None:
    if not context.systemctl.is_enabled("cosmic-greeter-daemon"):
        return None
    return CosmicGreeter(enable=True)
