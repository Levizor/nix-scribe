from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class SystemdBoot(NixModule, prefix="boot.loader.systemd-boot"):
    """systemd-boot UEFI Bootloader Configuration"""

    enable: bool = option(default=False)
    consoleMode: str | None = option()
    editor: bool | None = option()
    sortKey: str | None = option()
    xbootldrMountPoint: str | None = option()
