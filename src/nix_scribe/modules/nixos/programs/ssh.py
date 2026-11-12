from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Ssh(NixModule, prefix="programs.ssh", claims={"openssh"}):
    """OpenSSH Client Configuration"""

    forwardX11: bool | None = option()
    startAgent: bool = option()
    extraConfig: str = option()
