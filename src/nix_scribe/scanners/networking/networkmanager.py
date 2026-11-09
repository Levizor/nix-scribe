import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_types import quote_keys_with_dots
from nix_scribe.lib.parsers.ini import parse_bool, parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.networking.networkmanager import (
    NetworkManager,
    NetworkManagerWifi,
)

logger = logging.getLogger(__name__)

NETWORKMANAGER_CONFIG_PATHS = [
    "/etc/NetworkManager/NetworkManager.conf",
    "/etc/NetworkManager/conf.d",
]

VALID_DNS_MODES = {"default", "dnsmasq", "systemd-resolved", "none"}
VALID_DHCP_BACKENDS = {"dhcpcd", "internal"}
VALID_WIFI_BACKENDS = {"wpa_supplicant", "iwd"}

networkmanager = Scanner(
    "networking.networkmanager",
    description="NetworkManager configuration",
)


def _parse_powersave(val: Any) -> bool | None:
    s = str(val).lower()
    if s in ("3", "true", "yes"):
        return True
    if s in ("2", "false", "no"):
        return False
    return None


@networkmanager.scanner()
def scan(context: SystemContext) -> NetworkManager | None:
    if not context.systemctl.is_enabled("NetworkManager"):
        return None

    mod = NetworkManager(enable=True)

    reader = ConfigReader(context, parse_ini)
    raw_config = reader.read_merge_configs_from_paths_list(NETWORKMANAGER_CONFIG_PATHS)
    settings = {sec: dict(opts) for sec, opts in raw_config.items()}

    main = settings.get("main", {})
    if main.get("dns") in VALID_DNS_MODES:
        mod.dns = main.pop("dns")
    if main.get("dhcp") in VALID_DHCP_BACKENDS:
        mod.dhcp = main.pop("dhcp")

    wifi = NetworkManagerWifi()
    conn = settings.get("connection", {})
    if (
        "wifi.powersave" in conn
        and (ps := _parse_powersave(conn["wifi.powersave"])) is not None
    ):
        wifi.powersave = ps
        conn.pop("wifi.powersave")

    device = settings.get("device", {})
    if (
        "wifi.scan-rand-mac-address" in device
        and (rand := parse_bool(device["wifi.scan-rand-mac-address"])) is not None
    ):
        wifi.scanRandMacAddress = rand
        device.pop("wifi.scan-rand-mac-address")
    if device.get("wifi.backend") in VALID_WIFI_BACKENDS:
        wifi.backend = device.pop("wifi.backend")

    if wifi.to_dict():
        mod.wifi = wifi

    if clean_settings := {s: opts for s, opts in settings.items() if opts}:
        mod.settings = quote_keys_with_dots(clean_settings)

    return mod
