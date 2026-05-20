from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

gnome = Module("services.desktopManager.gnome")


@gnome.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {"enable": bool(context.find_executable_path("gnome-shell"))}


@gnome.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="gnome",
        description="Gnome desktop environment",
        data={"services.desktopManager.gnome": {"enable": True}},
    )
