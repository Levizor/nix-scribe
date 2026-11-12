from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Networking(NixModule, prefix="networking"):
    """Basic networking configuration"""

    hostName: str | None = option()
    enableIPv6: bool = option("enableIpv6", default=True)
    hosts: dict[str, list[str]] = option()
    nameservers: list[str] = option()
    search: list[str] = option()
    domain: str | None = option()
    useDHCP: bool = option(default=True, claims={"dhcpcd"})
    useNetworkd: bool = option()
    timeServers: list[str] = option()
