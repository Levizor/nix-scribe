from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class Networking(NixModule, prefix="networking"):
    """Basic networking configuration"""

    hostName: str | None = option()
    enableIPv6: bool = option("enableIpv6", default=True)
    hosts: dict[str, list[str]] = option(default={})
    nameservers: list[str] = option(default=[])
    search: list[str] = option(default=[])
    domain: str | None = option()
    useDHCP: bool = option(default=False, claims={"dhcpcd"})
    useNetworkd: bool = option(default=False)
    timeServers: list[str] = option(default=[])
