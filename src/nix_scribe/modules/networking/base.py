import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import BaseOptionBlock, SimpleOptionBlock
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.networking import parse_hosts, parse_resolv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)


class NetworkingScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
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

        if context.path_exists("/proc/sys/net/ipv6/conf/all/disable_ipv6"):
            disable_ipv6 = context.read_file(
                "/proc/sys/net/ipv6/conf/all/disable_ipv6"
            ).strip()
            if disable_ipv6 == "1":
                ir["enableIpv6"] = False

        if context.path_exists("/etc/hosts"):
            hosts_reader = ConfigReader(context, parse_hosts)
            raw_hosts = hosts_reader.read_config("/etc/hosts")
            ir["hosts"] = self._filter_hosts(raw_hosts, ir.get("hostName"))

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

    def _filter_hosts(
        self, hosts: dict[str, list[str]], hostname: str | None
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


class NetworkingMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> BaseOptionBlock | None:
        if not ir:
            return None

        networking = {}

        if ir.get("hostName"):
            networking["hostName"] = ir["hostName"]

        if ir.get("enableIpv6") is False:
            networking["enableIpv6"] = False

        if ir.get("hosts"):
            networking["hosts"] = {f'"{k}"': v for k, v in ir["hosts"].items()}

        if ir.get("nameservers"):
            networking["nameservers"] = ir["nameservers"]

        if ir.get("search"):
            networking["search"] = ir["search"]

        if ir.get("domain"):
            networking["domain"] = ir["domain"]

        if ir.get("useDHCP"):
            networking["useDHCP"] = True

        if ir.get("useNetworkd"):
            networking["useNetworkd"] = True

        if ir.get("timeServers"):
            networking["timeServers"] = ir["timeServers"]

        if not networking:
            return None

        return SimpleOptionBlock(
            name="networking",
            description="Basic networking configuration",
            data={"networking": networking},
        )


module = Module("networking", NetworkingScanner(), NetworkingMapper())
