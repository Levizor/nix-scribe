from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

cosmic = Module("services.desktopManager.cosmic")


@cosmic.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {
        "enable": bool(
            context.find_executable_path("cosmic-session")
            or context.find_executable_path("cosmic-comp")
        )
    }


@cosmic.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="cosmic",
        description="Cosmic desktop environment",
        data={"services.desktopManager.cosmic": {"enable": True}},
    )
