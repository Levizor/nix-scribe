from __future__ import annotations

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.nix_module import NixModule, option


class Grub(NixModule, prefix="boot.loader.grub", claims={"grub2"}):
    """GRUB Bootloader Configuration"""

    enable: bool = option(default=True, omit_default=False)
    efiSupport: bool = option()
    zfsSupport: bool = option()
    default: str = option(default="0")
    timeoutStyle: str | None = option()
    useOSProber: bool = option()
    enableCryptodisk: bool = option()
    splashImage: Asset | None = option()
