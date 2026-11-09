from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Kernel(NixModule, prefix="boot"):
    """Kernel Modules and Parameters Configuration"""

    kernelModules: list[str] = option(default=[])
    blacklistedKernelModules: list[str] = option(default=[])
    kernelParams: list[str] = option(default=[])
    extraModprobeConfig: str = option(default="")
