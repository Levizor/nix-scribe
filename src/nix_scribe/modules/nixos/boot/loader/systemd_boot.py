from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class SystemdBoot(NixModule, prefix="boot.loader.systemd-boot"):
    """systemd-boot UEFI Bootloader Configuration"""

    enable: bool = option()
    consoleMode: str = option()
    editor: bool = option()
    sortKey: str = option()
    xbootldrMountPoint: str = option()
