import logging

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.parsers.kv import is_truthy, parse_kv
from nix_scribe.lib.parsers.networking import parse_hosts, parse_resolv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.networking.networking import Networking

logger = logging.getLogger(__name__)

networking = Scanner(
    "networking",
    description="Basic networking configuration",
)


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
def scan(context: SystemContext) -> Networking | None:
    mod = Networking()

    if context.path_exists("/etc/hostname"):
        host = context.read_file("/etc/hostname").strip()
        if host:
            mod.hostName = host

    sysctl_reader = ConfigReader(context, parse_kv)
    sysctl_config = sysctl_reader.read_merge_configs_from_paths_list(
        ["/etc/sysctl.conf", "/etc/sysctl.d"]
    )
    if is_truthy(sysctl_config.get("net.ipv6.conf.all.disable_ipv6")) or is_truthy(
        sysctl_config.get("net.ipv6.conf.default.disable_ipv6")
    ):
        mod.enableIPv6 = False

    if context.path_exists("/etc/hosts"):
        hosts_reader = ConfigReader(context, parse_hosts)
        raw_hosts = hosts_reader.read_config("/etc/hosts")
        filtered_hosts = _filter_hosts(raw_hosts, mod.hostName)
        if filtered_hosts:
            mod.hosts = {f'"{k}"': v for k, v in filtered_hosts.items()}

    if context.path_exists("/etc/resolv.conf"):
        resolv_reader = ConfigReader(context, parse_resolv)
        dns_data = resolv_reader.read_config("/etc/resolv.conf")
        if not dns_data.get("is_dynamic", False):
            mod.nameservers = dns_data["nameservers"]
            mod.search = dns_data["search"]
            mod.domain = dns_data["domain"]

    if context.systemctl.is_enabled("dhcpcd"):
        mod.useDHCP = True

    if context.systemctl.is_enabled("systemd-networkd"):
        mod.useNetworkd = True

    if context.path_exists("/etc/systemd/timesyncd.conf"):
        try:
            content = context.read_file("/etc/systemd/timesyncd.conf")
            config = parse_ini(content)
            if "Time" in config and "NTP" in config["Time"]:
                ntp_value = config["Time"]["NTP"]
                if ntp_value:
                    mod.timeServers = ntp_value.split()
        except Exception as e:
            logger.warning(f"Failed to parse /etc/systemd/timesyncd.conf: {e}")

    if not mod.to_dict():
        return None

    return mod
