import logging

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.ini import parse_ini
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.git import Git, GitLfs

logger = logging.getLogger(__name__)

git = Scanner(
    "programs.git",
    description="Git version control system",
)

GITCONFIG_PATH = "/etc/gitconfig"


def _check_prompt_enabled(context: SystemContext) -> bool:
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


@git.scanner()
def scan(context: SystemContext) -> Git | None:
    if not context.find_executable_path("git"):
        return None

    mod = Git(enable=True)

    if context.find_executable_path("git-lfs"):
        mod.lfs = GitLfs(enable=True)

    if context.path_exists(GITCONFIG_PATH):
        try:
            content = context.read_file(GITCONFIG_PATH)
            mod.config = parse_ini(content)
        except Exception as e:
            logger.warning(f"Failed to parse {GITCONFIG_PATH}: {e}")

    mod.prompt_enable = _check_prompt_enabled(context)

    return mod
