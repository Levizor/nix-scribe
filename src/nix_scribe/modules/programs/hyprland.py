from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

hyprland = Module("programs.hyprland")


@hyprland.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {"enable": bool(context.find_executable_path("Hyprland"))}


@hyprland.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="hyprland",
        description="Hyprland compositor",
        data={"programs.hyprland": {"enable": True}},
    )
