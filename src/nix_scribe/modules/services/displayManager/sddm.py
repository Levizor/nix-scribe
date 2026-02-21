import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.parsers import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)


class SddmScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {}

        if not context.systemctl.is_enabled("sddm"):
            return ir

        ir["enable"] = True

        config_paths = [
            "/etc/sddm.conf",
            "/etc/sddm.conf.d/",
        ]

        try:
            config_reader = ConfigReader(context, parse_ini)
            ir["config"] = config_reader.read_merge_configs_from_paths_list(
                config_paths
            )
        except Exception as e:
            logger.warning(f"Failed to parse GDM config: {e}")

        return ir


class SddmMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        data: dict[str, Any] = {"enable": True}

        config = ir.get("config", {})

        general_section = config.get("General", {})
        theme_section = config.get("Theme", {})

        # wayland
        if "DisplayServer" in general_section:
            val = general_section["DisplayServer"].lower()
            if val == "wayland":
                data["wayland.enable"] = True
            elif val == "x11":
                data["wayland.enable"] = False

        # numlock
        if "Numlock" in general_section:
            val = general_section["Numlock"].lower()
            if val == "on":
                data["autoNumlock"] = True
            elif val == "off":
                data["autoNumlock"] = False

        if "Current" in theme_section:
            data["theme"] = theme_section["Current"]

        # settings
        settings = {}
        for section, keys in config.items():
            filtered = {}
            for k, v in keys.items():
                if section == "General" and k in ["DisplayServer", "Numlock"]:
                    continue
                if section == "Theme" and k in ["Current"]:
                    continue
                if section not in settings:
                    settings[section] = {}

                filtered[k] = v

            if filtered:
                settings[section] = filtered

        if settings:
            data["settings"] = settings

        return SimpleOptionBlock(
            name="services/desktopManager/sddm",
            description="Simple Desktop Display Manager",
            data={"services.displayManager.sddm": data},
        )


module = Module("sddm", SddmScanner(), SddmMapper())
