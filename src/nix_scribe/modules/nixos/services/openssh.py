from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class OpenSSH(NixModule, prefix="services.openssh", claims={"openssh"}):
    """OpenSSH Secure Shell Service"""

    enable: bool = option()
    ports: list[int] = option(default=[22], omit_default=False)
    hostKeys: list[dict[str, Any]] = option()
    settings: dict[str, Any] = option()
