from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Bash(NixModule, prefix="programs.bash", claims={"bash"}):
    """Bash Shell Configuration"""

    enable: bool = option(default=False)
    interactiveShellInit: str = option(default="")
    loginShellInit: str = option(default="")
    logout: str = option(default="")
    promptInit: str | None = option()
    shellAliases: dict[str, str] = option(default={})
