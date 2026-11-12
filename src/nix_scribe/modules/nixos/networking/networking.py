from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Networking(NixModule, prefix="networking"):
    """Basic networking configuration"""

    hostName: str = option()
    enableIPv6: bool = option("enableIpv6")
    hosts: dict[str, list[str]] = option()
    nameservers: list[str] = option()
    search: list[str] = option()
    domain: str = option()
    useDHCP: bool = option(claims={"dhcpcd"})
    useNetworkd: bool = option()
    timeServers: list[str] = option()
