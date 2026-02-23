from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class HyprlandScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        return {"enable": bool(context.find_executable_path("Hyprland"))}


class HyprlandMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        return SimpleOptionBlock(
            name="programs/hyprland",
            description="Hyprland compositor",
            data={"programs.hyprland.enable": True},
        )


module = Module("hyprland", HyprlandScanner(), HyprlandMapper())
