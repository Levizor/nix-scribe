import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.displayManager.gdm import Gdm

logger = logging.getLogger(__name__)

gdm = Scanner("services.displayManager.gdm")

GDM_CONFIG_PATHS = [
    "/etc/gdm/custom.conf",
    "/etc/gdm3/custom.conf",
    "/etc/gdm/daemon.conf",
]


@gdm.scanner()
def scan(context: SystemContext) -> Gdm | None:
    if not context.systemctl.is_enabled("gdm"):
        return None

    mod = Gdm(enable=True)

    config: dict[str, Any] = {}
    try:
        config_reader = ConfigReader(context, parse_ini)
        config = config_reader.read_merge_configs_from_paths_list(GDM_CONFIG_PATHS)
    except Exception as e:
        logger.warning(f"Failed to parse GDM config: {e}")

    daemon_section = config.get("daemon", {})
    debug_section = config.get("debug", {})

    if "WaylandEnable" in daemon_section:
        val = str(daemon_section["WaylandEnable"]).lower()
        if val == "false":
            mod.wayland = False
        elif val == "true":
            mod.wayland = True

    if "TimedLoginDelay" in daemon_section:
        try:
            mod.autoLogin_delay = int(daemon_section["TimedLoginDelay"])
        except ValueError:
            pass

    if "Enable" in debug_section and str(debug_section["Enable"]).lower() == "true":
        mod.debug = True

    settings: dict[str, Any] = {}
    for section, keys in config.items():
        filtered = {}
        for k, v in keys.items():
            if section == "daemon" and k in ["WaylandEnable", "TimedLoginDelay"]:
                continue
            if section == "debug" and k in ["Enable"]:
                continue
            filtered[k] = v
        if filtered:
            settings[section] = filtered

    if settings:
        mod.settings = settings

    return mod
