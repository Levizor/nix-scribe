import logging
import re
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

bash = Module("programs.bash")


def _parse_rc(content: str) -> tuple[str, dict[str, str], bool]:
    """
    Extracts aliases and PS1 from bashrc, returning (remaining_content, aliases, prompt).
    """
    aliases = {}
    remaining_lines = []
    prompt_set = False

    # regex for alias name='command'
    alias_re = re.compile(
        r'^\s*alias(?:\s+--)?\s+([^=\s]+)=(?:([\'"])(.*?)\2|([^\s]+))'
    )

    # regex for ps1='prompt'
    ps1_re = re.compile(r".*PS1.*")

    for line in content.splitlines():
        stripped = line.strip()

        prompt_match = ps1_re.match(stripped)
        alias_match = alias_re.match(stripped)

        if alias_match:
            groups = alias_match.groups()
            name = groups[0]
            if groups[2] is not None:  # quoted
                value = groups[2]
            else:  # unquoted
                value = groups[3]
            aliases[name] = value
            continue

        if prompt_match:
            prompt_set = True

        remaining_lines.append(line)

    return "\n".join(remaining_lines).strip(), aliases, prompt_set


@bash.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ir = {
        "enable": context.find_executable_path("bash") is not None,
        "interactiveShellInit": "",
        "loginShellInit": "",
        "logout": "",
        "shellAliases": {},
    }

    if not ir["enable"]:
        return ir

    if context.path_exists("/etc/profile"):
        ir["loginShellInit"] = context.read_file("/etc/profile")

    for path in ["/etc/bash_logout", "/etc/bash/bash_logout"]:
        if context.path_exists(path):
            ir["logout"] = context.read_file(path)
            break

    rc_content = ""
    for path in ["/etc/bash.bashrc", "/etc/bashrc"]:
        if context.path_exists(path):
            rc_content = context.read_file(path)
            break

    if rc_content:
        ir["interactiveShellInit"], ir["shellAliases"], prompt_set = _parse_rc(
            rc_content
        )

        if prompt_set:
            ir["promptInit"] = ""

    return ir


@bash.mapper()
def map(ir: dict[str, Any]) -> SimpleOptionBlock | None:
    if not ir.get("enable"):
        return None

    # Copy IR but remove enable to avoid duplication in nested dict
    data = ir.copy()
    data.pop("enable", None)

    bash_config = {"enable": True, **data}

    return SimpleOptionBlock(
        name="bash",
        description="Bash Shell Configuration",
        data={"programs.bash": bash_config},
    )
