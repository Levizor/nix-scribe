from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

plasma_login_manager = Module("services.displayManager.plasma-login-manager")


@plasma_login_manager.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    is_enabled = context.systemctl.is_enabled("plasmalogin")

    config_reader = ConfigReader(context, parse_ini)
    config = config_reader.read_merge_configs_from_paths_list(
        ["/etc/plasmalogin.conf", "/etc/plasmalogin.conf.d/"]
    )

    ir = {"enable": is_enabled, "config": config}

    return ir


@plasma_login_manager.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    plasmalogin_config: dict[str, Any] = {
        "enable": True,
    }

    settings = ir.get("config", {})

    if settings:
        plasmalogin_config["settings"] = settings

    return ConfigFragment(
        name="plasma-login-manager",
        description="Plasma Login Manager (Greeter)",
        data={"services.displayManager.plasma-login-manager": plasmalogin_config},
    )
