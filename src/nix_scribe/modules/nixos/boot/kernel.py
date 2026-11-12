from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Kernel(NixModule, prefix="boot"):
    """Kernel Modules and Parameters Configuration"""

    kernelModules: list[str] = option()
    blacklistedKernelModules: list[str] = option()
    kernelParams: list[str] = option()
    extraModprobeConfig: str = option()
