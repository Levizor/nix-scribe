import logging

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.security.rtkit import Rtkit

logger = logging.getLogger(__name__)

rtkit = Scanner(
    "security.rtkit",
    description="RealtimeKit system service",
)


def _parse_exec_start_args(content: str) -> list[str]:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("ExecStart="):
            cmd_line = line.split("=", 1)[1]
            parts = cmd_line.split()
            if len(parts) > 1:
                return parts[1:]
    return []


@rtkit.scanner()
def scan(context: SystemContext) -> Rtkit | None:
    if not context.systemctl.exists("rtkit-daemon"):
        return None

    mod = Rtkit(enable=True)

    service_paths = [
        "/lib/systemd/system/rtkit-daemon.service",
        "/usr/lib/systemd/system/rtkit-daemon.service",
        "/etc/systemd/system/rtkit-daemon.service",
    ]

    for path in service_paths:
        if context.path_exists(path):
            try:
                content = context.read_file(path)
                args = _parse_exec_start_args(content)
                if args:
                    mod.args = args
                break
            except Exception as e:
                logger.warning(f"Failed to read or parse {path}: {e}")

    return mod
