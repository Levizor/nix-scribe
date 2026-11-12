from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.displayManager.plasma_login_manager import (
    PlasmaLoginManager,
)

plasma_login_manager = Scanner("services.displayManager.plasma-login-manager")

PLASMALOGIN_CONFIG_PATHS = [
    "/etc/plasmalogin.conf",
    "/etc/plasmalogin.conf.d/",
]


@plasma_login_manager.scanner()
def scan(context: SystemContext) -> PlasmaLoginManager | None:
    if not context.systemctl.is_enabled("plasmalogin"):
        return None

    config_reader = ConfigReader(context, parse_ini)
    config = config_reader.read_merge_configs_from_paths_list(PLASMALOGIN_CONFIG_PATHS)

    mod = PlasmaLoginManager(enable=True)
    if config:
        mod.settings = config

    return mod
