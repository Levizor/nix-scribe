from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class SubUidRange(NixModule):
    startUid: int = option()
    count: int = option()


class SubGidRange(NixModule):
    startGid: int = option()
    count: int = option()


class UserEntry(NixModule):
    isNormalUser: bool = option()
    uid: int = option()
    description: str = option()
    home: str = option()
    group: str = option()
    extraGroups: list[str] = option()
    hashedPassword: str = option()
    expires: str = option()
    shell: Any = option(arguments={"pkgs"})
    authorized_keys: list[str] = option("openssh.authorizedKeys.keys")
    subUidRanges: list[SubUidRange] = option()
    subGidRanges: list[SubGidRange] = option()


class Users(NixModule, prefix="users.users"):
    """User accounts and subordinate ID ranges"""

    users: dict[str, UserEntry] = option(inline=True)
