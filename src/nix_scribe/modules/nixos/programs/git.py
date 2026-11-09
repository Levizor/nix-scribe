from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class GitLfs(NixModule, claims={"git-lfs"}):
    enable: bool = option(default=False)
    enablePureSSHTransfer: bool = option(default=False)


class Git(NixModule, prefix="programs.git", claims={"git"}):
    """Git version control system"""

    enable: bool = option(default=False)
    prompt_enable: bool = option("prompt.enable", default=False)
    config: dict[str, Any] = option(default={})
    lfs: GitLfs | None = option()
