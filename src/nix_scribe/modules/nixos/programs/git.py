from __future__ import annotations

from typing import Any

from nix_scribe.lib.nix_module import NixModule, option


class GitLfs(NixModule, claims={"git-lfs"}):
    enable: bool = option()
    enablePureSSHTransfer: bool = option()


class Git(NixModule, prefix="programs.git", claims={"git"}):
    """Git version control system"""

    enable: bool = option()
    prompt_enable: bool = option("prompt.enable")
    config: dict[str, Any] = option()
    lfs: GitLfs | None = option()
