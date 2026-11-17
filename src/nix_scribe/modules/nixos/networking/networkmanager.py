from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class NetworkManagerWifi(NixModule):
    powersave: bool = option()
    scanRandMacAddress: bool = option()
    backend: str = option()


class NetworkManager(
    NixModule, prefix="networking.networkmanager", claims={"networkmanager"}
):
    """NetworkManager configuration"""

    enable: bool = option()
    dns: str = option()
    dhcp: str = option()
    wifi: NetworkManagerWifi = option()
    settings: dict[str, Any] = option()
