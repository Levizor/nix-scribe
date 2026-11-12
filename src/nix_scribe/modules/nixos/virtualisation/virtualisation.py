from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class VmVariantVirtualisation(NixModule):
    cores: int = option()
    memorySize: int = option()
    diskSize: int = option()
    qemu_options: list[str] = option("qemu.options")


class Virtualisation(NixModule, prefix="virtualisation.vmVariant"):
    """virtualisation options for testing the machine"""

    virtualisation: VmVariantVirtualisation = option()
