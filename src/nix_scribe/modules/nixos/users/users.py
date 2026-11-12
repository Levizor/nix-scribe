from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class SubUidRange(NixModule):
    startUid: int | None = option()
    count: int | None = option()


class SubGidRange(NixModule):
    startGid: int | None = option()
    count: int | None = option()


class UserEntry(NixModule):
    isNormalUser: bool = option()
    uid: int | None = option()
    description: str = option(omit_default=False)
    home: str | None = option()
    group: str = option(default="users", omit_default=False)
    extraGroups: list[str] = option()
    hashedPassword: str | None = option()
    expires: str | None = option()
    shell: Any = option(arguments={"pkgs"})
    authorized_keys: list[str] = option("openssh.authorizedKeys.keys")
    subUidRanges: list[SubUidRange] = option()
    subGidRanges: list[SubGidRange] = option()


class Users(NixModule, prefix="users.users"):
    """User accounts and subordinate ID ranges"""

    users: dict[str, UserEntry] = option(inline=True)
