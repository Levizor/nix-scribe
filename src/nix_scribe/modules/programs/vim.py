import re
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

vim = Module("programs.vim")


def _is_default_editor(context: SystemContext) -> bool:
    if context.path_exists("/usr/bin/editor"):
        try:
            editor_path = context.readlink("/usr/bin/editor", recursive=True)
            if editor_path and ("vim" in editor_path.split("/")[-1]):
                return True
        except Exception:
            pass

    files_to_check = ["/etc/profile", "/etc/environment"]

    for file_path in files_to_check:
        if context.path_exists(file_path):
            content = context.read_file(file_path)
            # look for export EDITOR=vim or EDITOR=vim or EDITOR="/usr/bin/vim"
            if re.search(
                r"^\s*(export\s+)?(EDITOR|VISUAL)=['\"]?([^'\"\s]*/)?v(im|i)['\"]?\s*$",
                content,
                re.MULTILINE,
            ):
                return True

    return False


@vim.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    vim_path = context.find_executable_path("vim")
    ir = {"enable": bool(vim_path)}

    if not ir["enable"]:
        return ir

    ir["defaultEditor"] = _is_default_editor(context)

    return ir


@vim.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    data: dict[str, Any] = {"enable": True}

    if ir.get("defaultEditor"):
        data["defaultEditor"] = True

    return ConfigFragment(
        name="vim",
        description="Enable vim editor",
        data={"programs.vim": data},
    )
