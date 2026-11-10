from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.desktopManager.plasma6 import Plasma6

plasma6 = Scanner("services.desktopManager.plasma6")


@plasma6.scanner()
def scan(context: SystemContext) -> Plasma6 | None:
    if not context.find_executable_path("plasmashell"):
        return None
    return Plasma6(enable=True)
