import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.parsers import parse_ini
from nix_scribe.lib.parsers.ini import normalize_config
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)


class GdmScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {}

        gdm_bin = context.find_executable_path("gdm") or context.find_executable_path(
            "gdm3"
        )

        if not gdm_bin:
            return ir

        ir["enable"] = True

        config_paths = [
            "/etc/gdm/custom.conf",
            "/etc/gdm3/custom.conf",
            "/etc/gdm/daemon.conf",
        ]

        target_conf = [path for path in config_paths if context.path_exists(path)]
        if target_conf:
            target_conf = target_conf[0]
            try:
                ir["config"] = parse_ini(context.read_file(target_conf))
            except Exception as e:
                logger.warning(f"Failed to parse GDM config at {target_conf}: {e}")

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
            data["settings"] = normalize_config(settings)

        return SimpleOptionBlock(
            name="services/displayManager/gdm",
            description="Gnome display manager",
            data={"services.displayManager.gdm": data},
        )


module = Module("gdm", GdmScanner(), GdmMapper())
