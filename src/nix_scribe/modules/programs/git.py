import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)

GITCONFIG_PATH = "/etc/gitconfig"


class GitScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        git_path = context.find_executable_path("git")
        ir: dict[str, Any] = {"enable": bool(git_path)}

        if not ir["enable"]:
            return ir

        lfs_path = context.find_executable_path("git-lfs")
        if lfs_path:
            ir["lfs"] = {"enable": True}

            # TODO enablePureSSHTransfer

        if context.path_exists(GITCONFIG_PATH):
            try:
                content = context.read_file(GITCONFIG_PATH)
                ir["config"] = parse_ini(content)
            except Exception as e:
                logger.warning(f"Failed to parse {GITCONFIG_PATH}: {e}")

        ir["promptEnable"] = self._check_prompt_enabled(context)

        return ir

    def _check_prompt_enabled(self, context: SystemContext) -> bool:
        # check if git-prompt is mentioned in common shell init files
        for shell_init in ["/etc/bashrc", "/etc/bash.bashrc", "/etc/profile"]:
            if context.path_exists(shell_init):
                try:
                    content = context.read_file(shell_init)
                    if (
                        "__git_ps1" in content
                        or "git-prompt.sh" in content
                        or "git-sh-prompt" in content
                    ):
                        return True
                except Exception:
                    pass
        return False


class GitMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        git_config = {"enable": True}

        if ir.get("promptEnable"):
            git_config["prompt.enable"] = True

        if "config" in ir and ir["config"]:
            git_config["config"] = ir["config"]

        if ir.get("lfs", {}).get("enable"):
            git_config["lfs.enable"] = True
            if ir["lfs"].get("enablePureSSHTransfer"):
                git_config["lfs.enablePureSSHTransfer"] = True

        return SimpleOptionBlock(
            name="git",
            description="Git version control system",
            data={"programs.git": git_config},
        )


module = Module("git", GitScanner(), GitMapper())
