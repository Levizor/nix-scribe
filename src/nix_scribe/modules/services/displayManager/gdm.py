import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.parsers import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)


class GdmScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {}

        if not context.systemctl.is_enabled("gdm"):
            return ir

        ir["enable"] = True

        config_paths = [
            "/etc/gdm/custom.conf",
            "/etc/gdm3/custom.conf",
            "/etc/gdm/daemon.conf",
        ]

        try:
            config_reader = ConfigReader(context, parse_ini)
            ir["config"] = config_reader.read_merge_configs_from_paths_list(
                config_paths
            )
        except Exception as e:
            logger.warning(f"Failed to parse GDM config: {e}")

        return ir


class GdmMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        data: dict[str, Any] = {"enable": True}

        config = ir.get("config", {})

        daemon_section = config.get("daemon", {})
        debug_section = config.get("debug", {})

        # wayland
        if "WaylandEnable" in daemon_section:
            val = daemon_section["WaylandEnable"].lower()
            if val == "false":
                data["wayland"] = False
            elif val == "true":
                data["wayland"] = True

        # autologin
        if "TimedLoginDelay" in daemon_section:
            try:
                delay = int(daemon_section["TimedLoginDelay"])
                data["autoLogin.delay"] = delay
            except ValueError:
                pass

        # debug
        if "Enable" in debug_section and debug_section["Enable"].lower() == "true":
            data["debug"] = True

        # settings
        settings = {}
        for section, keys in config.items():
            filtered = {}
            for k, v in keys.items():
                if section == "daemon" and k in ["WaylandEnable", "TimedLoginDelay"]:
                    continue
                if section == "debug" and k in ["Enable"]:
                    continue
                if section not in settings:
                    settings[section] = {}

                filtered[k] = v
            if filtered:
                settings[section] = filtered

        if settings:
            data["settings"] = settings

        return SimpleOptionBlock(
            name="services/displayManager/gdm",
            description="Gnome display manager",
            data={"services.displayManager.gdm": data},
        )


module = Module("gdm", GdmScanner(), GdmMapper())
