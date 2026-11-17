from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Bash(NixModule, prefix="programs.bash", claims={"bash"}):
    """Bash Shell Configuration"""

    enable: bool = option()
    interactiveShellInit: str = option()
    loginShellInit: str = option()
    logout: str = option()
    promptInit: str = option()
    shellAliases: dict[str, str] = option()
