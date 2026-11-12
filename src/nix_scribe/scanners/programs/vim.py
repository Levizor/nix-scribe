import re

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.vim import Vim

vim = Scanner("programs.vim")


def _is_default_editor(context: SystemContext) -> bool:
    if context.path_exists("/usr/bin/editor"):
        try:
            editor_path = context.readlink("/usr/bin/editor", recursive=True)
            if editor_path and ("vim" in editor_path.split("/")[-1]):
                return True
        except Exception:
            pass

    for file_path in ["/etc/profile", "/etc/environment"]:
        if context.path_exists(file_path):
            content = context.read_file(file_path)
            if re.search(
                r"^\s*(export\s+)?(EDITOR|VISUAL)=['\"]?([^'\"\s]*/)?v(im|i)['\"]?\s*$",
                content,
                re.MULTILINE,
            ):
                return True

    return False


@vim.scanner()
def scan(context: SystemContext) -> Vim | None:
    if not context.find_executable_path("vim"):
        return None

    mod = Vim(enable=True)
    if _is_default_editor(context):
        mod.defaultEditor = True

    return mod
