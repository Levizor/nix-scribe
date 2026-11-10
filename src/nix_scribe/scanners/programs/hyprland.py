from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.hyprland import Hyprland

hyprland = Scanner("programs.hyprland")


@hyprland.scanner()
def scan(context: SystemContext) -> Hyprland | None:
    if not context.find_executable_path("Hyprland"):
        return None

    return Hyprland(enable=True)
