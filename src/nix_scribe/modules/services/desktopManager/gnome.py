from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class GnomeScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        return {"enable": bool(context.find_executable_path("gnome-shell"))}


class GnomeMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        return SimpleOptionBlock(
            name="services/desktopManager/gnome",
            description="Gnome desktop environment",
            data={"services.desktopManager.gnome.enable": True},
        )


module = Module("gnome", GnomeScanner(), GnomeMapper())
