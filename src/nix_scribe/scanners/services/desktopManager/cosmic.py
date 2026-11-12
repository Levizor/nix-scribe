from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.desktopManager.cosmic import Cosmic

cosmic = Scanner("services.desktopManager.cosmic")


@cosmic.scanner()
def scan(context: SystemContext) -> Cosmic | None:
    if not (
        context.find_executable_path("cosmic-session")
        or context.find_executable_path("cosmic-comp")
    ):
        return None
    return Cosmic(enable=True)
