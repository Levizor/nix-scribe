from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.fish import Fish

fish = Scanner("programs.fish")


@fish.scanner()
def scan(context: SystemContext) -> Fish | None:
    if not context.find_executable_path("fish"):
        return None

    return Fish(enable=True)
