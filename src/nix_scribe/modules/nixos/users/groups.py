from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class GroupEntry(NixModule):
    gid: int | None = option()
    members: list[str] = option()


class Groups(NixModule, prefix="users.groups"):
    """Existing user groups"""

    groups: dict[str, GroupEntry] = option(inline=True)
