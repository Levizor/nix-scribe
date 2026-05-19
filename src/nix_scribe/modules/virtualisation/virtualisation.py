from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.registry import Module

virtualisation = Module("virtualisation")


@virtualisation.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {}


@virtualisation.mapper()
def map(ir: dict[str, Any]) -> SimpleOptionBlock | None:
    return SimpleOptionBlock(
        name="virtualisation",
        description="virtualisation options for testing the machine",
        data={
            "virtualisation.vmVariant": {
                "virtualisation": {
                    "cores": 4,
                    "memorySize": 8128,
                    "diskSize": 10240,
                    "qemu.options": [
                        "-machine q35,accel=kvm,smm=off,vmport=off",
                        "-cpu host",
                        "-global kvm-pit.lost_tick_policy=discard",
                        "-vga none",
                        "-device virtio-vga-gl",
                        "-display sdl,gl=on",
                    ],
                }
            }
        },
    )
