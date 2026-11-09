import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.displayManager.sddm import Sddm

logger = logging.getLogger(__name__)

sddm = Scanner(
    "services.displayManager.sddm",
    description="Simple Desktop Display Manager",
)

SDDM_CONFIG_PATHS = [
    "/etc/sddm.conf",
    "/etc/sddm.conf.d/",
]


@sddm.scanner()
def scan(context: SystemContext) -> Sddm | None:
    if not context.systemctl.is_enabled("sddm"):
        return None

    mod = Sddm(enable=True)

    config: dict[str, Any] = {}
    try:
        config_reader = ConfigReader(context, parse_ini)
        config = config_reader.read_merge_configs_from_paths_list(SDDM_CONFIG_PATHS)
    except Exception as e:
        logger.warning(f"Failed to parse SDDM config: {e}")

    general_section = config.get("General", {})
    theme_section = config.get("Theme", {})

    if "DisplayServer" in general_section:
        val = str(general_section["DisplayServer"]).lower()
        if val == "wayland":
            mod.wayland_enable = True
        elif val == "x11":
            mod.wayland_enable = False

    if "Numlock" in general_section:
        val = str(general_section["Numlock"]).lower()
        if val == "on":
            mod.autoNumlock = True
        elif val == "off":
            mod.autoNumlock = False

    if "Current" in theme_section:
        mod.theme = theme_section["Current"]

    settings: dict[str, Any] = {}
    for section, keys in config.items():
        filtered = {}
        for k, v in keys.items():
            if section == "General" and k in ["DisplayServer", "Numlock"]:
                continue
            if section == "Theme" and k in ["Current"]:
                continue
            filtered[k] = v
        if filtered:
            settings[section] = filtered

    if settings:
        mod.settings = settings

    return mod
