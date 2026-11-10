import logging
import re

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.parsers.sudoers import parse_sudoers
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.security.sudo import Sudo

logger = logging.getLogger(__name__)

sudo = Scanner("security.sudo")

SUDOERS_PATH = "/etc/sudoers"
SUDOERS_DIR = "/etc/sudoers.d"

WHEEL_NOPASSWD_PATTERN = re.compile(
    r"^\s*%wheel\s+ALL\s*=\s*\([^)]*\)\s*NOPASSWD\s*:\s*ALL", re.IGNORECASE
)
ENV_KEEP_TERMINFO_PATTERN = re.compile(r"env_keep\s*\+?=\s*.*TERMINFO", re.IGNORECASE)


def _should_filter_line(line: str, mod: Sudo) -> bool:
    stripped = line.strip()

    if stripped.startswith("Defaults") and "secure_path" in stripped:
        return True

    if stripped == "Defaults env_reset":
        return True

    if (
        mod.wheelNeedsPassword is False
        and "%wheel" in stripped
        and "NOPASSWD" in stripped
    ):
        return True

    if mod.keepTerminfo and "env_keep" in stripped and "TERMINFO" in stripped:
        return True

    if stripped.startswith("root") and "ALL=(ALL" in stripped and "ALL" in stripped:
        return True

    return False


@sudo.scanner()
def scan(context: SystemContext) -> Sudo | None:
    has_sudoers_file = context.path_exists(SUDOERS_PATH)
    has_sudoers_dir = context.path_exists(SUDOERS_DIR)

    if not has_sudoers_file and not has_sudoers_dir:
        return None

    reader = ConfigReader(context, parse_sudoers)
    parsed = reader.read_merge_configs_from_paths_list([SUDOERS_PATH, SUDOERS_DIR])

    defaults = parsed.get("defaults", [])
    rules = parsed.get("rules", [])

    has_wheel_nopasswd = any(WHEEL_NOPASSWD_PATTERN.search(r) for r in rules)
    has_keep_terminfo = any(ENV_KEEP_TERMINFO_PATTERN.search(d) for d in defaults)

    mod = Sudo(
        enable=True,
        wheelNeedsPassword=not has_wheel_nopasswd,
        execWheelOnly=False,
        keepTerminfo=has_keep_terminfo,
    )

    sudo_bin = None
    for bpath in ["/usr/bin/sudo", "/bin/sudo", "/usr/sbin/sudo"]:
        if context.path_exists(bpath):
            sudo_bin = context.root_path(bpath)
            break

    if sudo_bin:
        try:
            st = sudo_bin.stat()
            if (st.st_mode & 0o001) == 0:
                mod.execWheelOnly = True
        except OSError:
            pass

    raw_lines = parsed.get("raw_lines", [])
    extra_lines = [line for line in raw_lines if not _should_filter_line(line, mod)]
    if extra_lines:
        mod.extraConfig = "\n".join(extra_lines)

    return mod
