from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class CosmicScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        return {
            "enable": bool(
                context.find_executable_path("cosmic-session")
                or context.find_executable_path("cosmic-comp")
            )
        }


class CosmicMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        return SimpleOptionBlock(
            name="services/desktopManager/cosmic",
            description="Cosmic desktop environment",
            data={"services.desktopManager.cosmic.enable": True},
        )


module = Module("cosmic", CosmicScanner(), CosmicMapper())
