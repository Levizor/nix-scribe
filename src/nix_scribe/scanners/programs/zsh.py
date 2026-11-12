from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.zsh import Zsh

zsh = Scanner("programs.zsh")


@zsh.scanner()
def scan(context: SystemContext) -> Zsh | None:
    if not context.find_executable_path("zsh"):
        return None

    return Zsh(enable=True)
