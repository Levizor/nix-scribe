from __future__ import annotations

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.nix_module import NixModule, option


class Grub(NixModule, prefix="boot.loader.grub", claims={"grub2"}):
    """GRUB Bootloader Configuration"""

    enable: bool = option(default=False)
    efiSupport: bool = option(default=False)
    zfsSupport: bool = option(default=False)
    default: str = option(default="0")
    timeoutStyle: str | None = option()
    useOSProber: bool = option(default=False)
    enableCryptodisk: bool = option(default=False)
    splashImage: Asset | None = option()
