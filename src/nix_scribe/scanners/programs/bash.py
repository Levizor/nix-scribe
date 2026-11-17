import logging
import re

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.bash import Bash

logger = logging.getLogger(__name__)

bash = Scanner("programs.bash")


def _parse_rc(content: str) -> tuple[str, dict[str, str], bool]:
    """Extracts aliases and PS1 from bashrc, returning (remaining_content, aliases, prompt)."""
    aliases: dict[str, str] = {}
    remaining_lines: list[str] = []
    prompt_set = False

    alias_re = re.compile(
        r'^\s*alias(?:\s+--)?\s+([^=\s]+)=(?:([\'"])(.*?)\2|([^\s]+))'
    )
    ps1_re = re.compile(r".*PS1.*")

    for line in content.splitlines():
        stripped = line.strip()

        prompt_match = ps1_re.match(stripped)
        alias_match = alias_re.match(stripped)

        if alias_match:
            groups = alias_match.groups()
            name = groups[0]
            value = groups[2] if groups[2] is not None else groups[3]
            aliases[name] = value
            continue

        if prompt_match:
            prompt_set = True

        remaining_lines.append(line)

    return "\n".join(remaining_lines).strip(), aliases, prompt_set


@bash.scanner()
def scan(context: SystemContext) -> Bash | None:
    if context.find_executable_path("bash") is None:
        return None

    mod = Bash(enable=True)

    if context.path_exists("/etc/profile"):
        mod.loginShellInit = context.read_file("/etc/profile")

    for path in ["/etc/bash_logout", "/etc/bash/bash_logout"]:
        if context.path_exists(path):
            mod.logout = context.read_file(path)
            break

    rc_content = ""
    for path in ["/etc/bash.bashrc", "/etc/bashrc"]:
        if context.path_exists(path):
            rc_content = context.read_file(path)
            break

    if rc_content:
        mod.interactiveShellInit, mod.shellAliases, prompt_set = _parse_rc(rc_content)
        if prompt_set:
            mod.promptInit = ""

    return mod
