from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

plasma6 = Module("services.desktopManager.plasma6")


@plasma6.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {"enable": bool(context.find_executable_path("plasmashell"))}


@plasma6.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="plasma6",
        description="KDE Plasma 6 Desktop Environment",
        data={"services.desktopManager.plasma6": {"enable": True}},
    )
