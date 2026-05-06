from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.registry import Module

cosmic_greeter = Module("services.displayManager.cosmic-greeter")


@cosmic_greeter.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {"enable": context.systemctl.is_enabled("cosmic-greeter-daemon")}


@cosmic_greeter.mapper()
def map(ir: dict[str, Any]) -> SimpleOptionBlock | None:
    if not ir.get("enable"):
        return None

    return SimpleOptionBlock(
        name="cosmic-greeter",
        description="cosmic-greeter displayManager",
        data={"services.displayManager.cosmic-greeter": {"enable": True}},
    )
