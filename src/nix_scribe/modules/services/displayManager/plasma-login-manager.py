from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class PlasmaLoginManagerScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        is_enabled = context.systemctl.is_enabled("plasmalogin")

        config_reader = ConfigReader(context, parse_ini)
        config = config_reader.read_merge_configs_from_paths_list(
            ["/etc/plasmalogin.conf", "/etc/plasmalogin.conf.d/"]
        )

        ir = {"enable": is_enabled, "config": config}

        return ir


class PlasmaLoginManagerMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        plasmalogin_config: dict[str, Any] = {
            "enable": True,
        }

        settings = ir.get("config", {})

        if settings:
            plasmalogin_config["settings"] = settings

        return SimpleOptionBlock(
            name="services/displayManager/plasma-login-manager",
            description="Plasma Login Manager (Greeter)",
            data={"services.displayManager.plasma-login-manager": plasmalogin_config},
        )


module = Module(
    "plasma-login-manager", PlasmaLoginManagerScanner(), PlasmaLoginManagerMapper()
)
