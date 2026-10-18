import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_types import quote_keys_with_dots
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.ini import parse_bool, parse_ini
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

NETWORKMANAGER_CONFIG_PATHS = [
    "/etc/NetworkManager/NetworkManager.conf",
    "/etc/NetworkManager/conf.d",
]

VALID_DNS_MODES = {"default", "dnsmasq", "systemd-resolved", "none"}
VALID_DHCP_BACKENDS = {"dhcpcd", "internal"}
VALID_WIFI_BACKENDS = {"wpa_supplicant", "iwd"}

networkmanager = Module("networking.networkmanager")


def _parse_powersave(val: Any) -> bool | None:
    s = str(val).lower()
    if s in ("3", "true", "yes"):
        return True
    if s in ("2", "false", "no"):
        return False
    return None


@networkmanager.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ir: dict[str, Any] = {
        "enable": False,
        "config": {},
    }

    if context.systemctl.is_enabled("NetworkManager"):
        ir["enable"] = True

    reader = ConfigReader(context, parse_ini)
    ir["config"] = reader.read_merge_configs_from_paths_list(
        NETWORKMANAGER_CONFIG_PATHS
    )

    return ir


@networkmanager.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    nm_config: dict[str, Any] = {"enable": True}
    settings = {sec: dict(opts) for sec, opts in ir.get("config", {}).items()}

    main = settings.get("main", {})
    if main.get("dns") in VALID_DNS_MODES:
        nm_config["dns"] = main.pop("dns")
    if main.get("dhcp") in VALID_DHCP_BACKENDS:
        nm_config["dhcp"] = main.pop("dhcp")

    wifi_config: dict[str, Any] = {}
    conn = settings.get("connection", {})
    if (
        "wifi.powersave" in conn
        and (ps := _parse_powersave(conn["wifi.powersave"])) is not None
    ):
        wifi_config["powersave"] = ps
        conn.pop("wifi.powersave")

    device = settings.get("device", {})
    if (
        "wifi.scan-rand-mac-address" in device
        and (rand := parse_bool(device["wifi.scan-rand-mac-address"])) is not None
    ):
        wifi_config["scanRandMacAddress"] = rand
        device.pop("wifi.scan-rand-mac-address")
    if device.get("wifi.backend") in VALID_WIFI_BACKENDS:
        wifi_config["backend"] = device.pop("wifi.backend")

    if wifi_config:
        nm_config["wifi"] = wifi_config

    if clean_settings := {s: opts for s, opts in settings.items() if opts}:
        nm_config["settings"] = quote_keys_with_dots(clean_settings)

    return ConfigFragment(
        name="networkmanager",
        description="NetworkManager configuration",
        data={"networking.networkmanager": nm_config},
        claims={"networkmanager"},
    )
