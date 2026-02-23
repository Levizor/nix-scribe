from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class CosmicGreeterScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        return {"enable": context.systemctl.is_enabled("cosmic-greeter-daemon")}


class CosmicGreeterMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        return SimpleOptionBlock(
            name="services/displayManager/cosmic-greeter",
            description="cosmic-greeter displayManager",
            data={"services.displayManager.cosmic-greeter.enable": True},
        )


module = Module("cosmic-greeter", CosmicGreeterScanner(), CosmicGreeterMapper())
