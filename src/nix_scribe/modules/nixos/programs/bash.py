from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Bash(NixModule, prefix="programs.bash", claims={"bash"}):
    """Bash Shell Configuration"""

    enable: bool = option(default=True, omit_default=False)
    interactiveShellInit: str = option()
    loginShellInit: str = option()
    logout: str = option()
    promptInit: str | None = option()
    shellAliases: dict[str, str] = option()
