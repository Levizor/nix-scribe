from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class NetworkManagerWifi(NixModule):
    powersave: bool | None = option()
    scanRandMacAddress: bool | None = option()
    backend: str | None = option()


class NetworkManager(
    NixModule, prefix="networking.networkmanager", claims={"networkmanager"}
):
    """NetworkManager configuration"""

    enable: bool = option(default=False)
    dns: str | None = option()
    dhcp: str | None = option()
    wifi: NetworkManagerWifi | None = option()
    settings: dict[str, Any] = option(default={})
