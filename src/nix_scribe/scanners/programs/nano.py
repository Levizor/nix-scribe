from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.nano import Nano

nano = Scanner("programs.nano")


def _is_default_nanorc(text: str) -> bool:
    for line in text.splitlines():
        sline = line.strip()
        if not sline or sline.startswith("#"):
            continue
        return False
    return True


@nano.scanner()
def scan(context: SystemContext) -> Nano | None:
    if not context.find_executable_path("nano"):
        return None

    mod = Nano(enable=True)

    if context.path_exists("/etc/nanorc"):
        content = context.read_file("/etc/nanorc")
        if not _is_default_nanorc(content):
            mod.nanorc = content

    return mod
