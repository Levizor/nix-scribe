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
    isNormalUser: bool = option(default=False)
    uid: int | None = option()
    description: str = option(default="", omit_default=False)
    home: str | None = option()
    group: str = option(default="users", omit_default=False)
    extraGroups: list[str] = option(default=[])
    hashedPassword: str | None = option()
    expires: str | None = option()
    shell: Any = option(arguments={"pkgs"})
    authorized_keys: list[str] = option("openssh.authorizedKeys.keys", default=[])
    subUidRanges: list[SubUidRange] = option(default=[])
    subGidRanges: list[SubGidRange] = option(default=[])


class Users(NixModule, prefix="users.users"):
    """User accounts and subordinate ID ranges"""

    users: dict[str, UserEntry] = option(inline=True, default={})
    bash_enable: bool = option("programs.bash.enable", default=False, root=True)
    zsh_enable: bool = option("programs.zsh.enable", default=False, root=True)
    fish_enable: bool = option("programs.fish.enable", default=False, root=True)
