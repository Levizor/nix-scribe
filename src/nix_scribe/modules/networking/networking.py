import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.kv import parse_kv
from nix_scribe.lib.parsers.networking import parse_hosts, parse_resolv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

networking = Module("networking")


def _filter_hosts(
    hosts: dict[str, list[str]], hostname: str | None
) -> dict[str, list[str]]:
    filtered = {}
    for ip, names in hosts.items():
        if ip == "127.0.0.1" and "localhost" in names and len(names) == 1:
            continue
        if ip == "::1" and "localhost" in names and len(names) == 1:
            continue
        if ip in ["127.0.0.1", "127.0.1.1"] and hostname in names:
            names = [n for n in names if n != hostname]
            if not names:
                continue

        filtered[ip] = names
    return filtered


@networking.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ir = {
        "hostName": None,
        "enableIpv6": True,
        "hosts": {},
        "nameservers": [],
        "search": [],
        "domain": None,
        "useDHCP": False,
        "useNetworkd": False,
        "timeServers": [],
    }

    if context.path_exists("/etc/hostname"):
        ir["hostName"] = context.read_file("/etc/hostname").strip()

    sysctl_reader = ConfigReader(context, parse_kv)
    sysctl_config = sysctl_reader.read_merge_configs_from_paths_list(
        ["/etc/sysctl.conf", "/etc/sysctl.d"]
    )
    if str(sysctl_config.get("net.ipv6.conf.all.disable_ipv6")).strip() in (
        "1",
        "true",
        "True",
    ) or str(sysctl_config.get("net.ipv6.conf.default.disable_ipv6")).strip() in (
        "1",
        "true",
        "True",
    ):
        ir["enableIpv6"] = False

    if context.path_exists("/etc/hosts"):
        hosts_reader = ConfigReader(context, parse_hosts)
        raw_hosts = hosts_reader.read_config("/etc/hosts")
        ir["hosts"] = _filter_hosts(raw_hosts, ir.get("hostName"))

    if context.path_exists("/etc/resolv.conf"):
        resolv_reader = ConfigReader(context, parse_resolv)
        dns_data = resolv_reader.read_config("/etc/resolv.conf")
        if not dns_data.get("is_dynamic", False):
            ir["nameservers"] = dns_data["nameservers"]
            ir["search"] = dns_data["search"]
            ir["domain"] = dns_data["domain"]

    if context.systemctl.is_enabled("dhcpcd"):
        ir["useDHCP"] = True

    if context.systemctl.is_enabled("systemd-networkd"):
        ir["useNetworkd"] = True

    if context.path_exists("/etc/systemd/timesyncd.conf"):
        try:
            content = context.read_file("/etc/systemd/timesyncd.conf")
            config = parse_ini(content)
            if "Time" in config and "NTP" in config["Time"]:
                ntp_value = config["Time"]["NTP"]
                if ntp_value:
                    ir["timeServers"] = ntp_value.split()
        except Exception as e:
            logger.warning(f"Failed to parse /etc/systemd/timesyncd.conf: {e}")

    return ir


@networking.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir:
        return None

    data = {}

    if ir.get("hostName"):
        data["hostName"] = ir["hostName"]

    if ir.get("enableIpv6") is False:
        data["enableIpv6"] = False

    if ir.get("hosts"):
        data["hosts"] = {f'"{k}"': v for k, v in ir["hosts"].items()}

    if ir.get("nameservers"):
        data["nameservers"] = ir["nameservers"]

    if ir.get("search"):
        data["search"] = ir["search"]

    if ir.get("domain"):
        data["domain"] = ir["domain"]

    if ir.get("useDHCP"):
        data["useDHCP"] = True

    if ir.get("useNetworkd"):
        data["useNetworkd"] = True

    if ir.get("timeServers"):
        data["timeServers"] = ir["timeServers"]

    if not data:
        return None

    return ConfigFragment(
        name="networking",
        description="Basic networking configuration",
        data={"networking": data},
    )
