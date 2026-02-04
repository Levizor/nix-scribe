from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class PlasmaScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        return {"enable": bool(context.find_executable_path("plasmashell"))}


class PlasmaMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        return SimpleOptionBlock(
            name="services/desktopManager/plasma6",
            description="KDE Plasma 6 Desktop Environment",
            data={"services.desktopManager.plasma6.enable": True},
        )


module = Module("plasma6", PlasmaScanner(), PlasmaMapper())
