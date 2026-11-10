from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.desktopManager.gnome import Gnome

gnome = Scanner("services.desktopManager.gnome")


@gnome.scanner()
def scan(context: SystemContext) -> Gnome | None:
    if not context.find_executable_path("gnome-shell"):
        return None
    return Gnome(enable=True)
