from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

cowsay = Module("fun.cowsay")


@cowsay.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {
        "enable": True,
        "message": "Moo! nix-scribe plugins work like a charm!",
    }


@cowsay.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None
    return ConfigFragment(
        name="cowsay",
        description="Fun Cowsay Plugin Module",
        data={
            "environment.sessionVariables": {
                "COWSAY_MOTD": ir["message"],
            }
        },
    )
