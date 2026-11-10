from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.virtualisation.virtualisation import (
    Virtualisation,
    VmVariantVirtualisation,
)

virtualisation = Scanner("virtualisation")


@virtualisation.scanner()
def scan(context: SystemContext) -> Virtualisation:
    return Virtualisation(
        virtualisation=VmVariantVirtualisation(
            cores=4,
            memorySize=8128,
            diskSize=10240,
            qemu_options=[
                "-machine q35,accel=kvm,smm=off,vmport=off",
                "-cpu host",
                "-global kvm-pit.lost_tick_policy=discard",
                "-vga none",
                "-device virtio-vga-gl",
                "-display sdl,gl=on",
            ],
        )
    )
