from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class VmVariantVirtualisation(NixModule):
    cores: int = option(default=1)
    memorySize: int = option(default=1024)
    diskSize: int | None = option()
    qemu_options: list[str] = option("qemu.options")


class Virtualisation(NixModule, prefix="virtualisation.vmVariant"):
    """virtualisation options for testing the machine"""

    virtualisation: VmVariantVirtualisation | None = option()
