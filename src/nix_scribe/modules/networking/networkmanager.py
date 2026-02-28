import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import BaseOptionBlock, SimpleOptionBlock
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)


class NetworkManagerScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {
            "enable": False,
            "config": {},
        }

        if context.systemctl.is_enabled("NetworkManager"):
            ir["enable"] = True

        reader = ConfigReader(context, parse_ini)
        ir["config"] = reader.read_merge_configs_from_paths_list(
            ["/etc/NetworkManager/NetworkManager.conf", "/etc/NetworkManager/conf.d"]
        )

        return ir


class NetworkManagerMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> BaseOptionBlock | None:
        if not ir.get("enable"):
            return None

        nm_config = {}
        settings = ir.get("config", {})

        nm_config["enable"] = True

        main_section = settings.get("main", {})
        if "dns" in main_section:
            nm_config["dns"] = main_section.pop("dns")
        if "dhcp" in main_section:
            nm_config["dhcp"] = main_section.pop("dhcp")

        wifi_config = {}
        connection_section = settings.get("connection", {})
        if "wifi.powersave" in connection_section:
            wifi_config["powersave"] = True

        device_section = settings.get("device", {})
        if "wifi.scan-rand-mac-address" in device_section:
            val = device_section.pop("wifi.scan-rand-mac-address")
            if isinstance(val, bool):
                wifi_config["scanRandMacAddress"] = val
            else:
                wifi_config["scanRandMacAddress"] = str(val).lower() in (
                    "yes",
                    "true",
                    "1",
                )

        if wifi_config:
            nm_config["wifi"] = wifi_config

        final_settings = {}
        for section, options in settings.items():
            if options:
                final_settings[section] = options

        if final_settings:
            nm_config["settings"] = final_settings

        return SimpleOptionBlock(
            name="networkmanager",
            description="NetworkManager configuration",
            data={"networking": {"networkmanager": nm_config}},
        )


module = Module("networkmanager", NetworkManagerScanner(), NetworkManagerMapper())
