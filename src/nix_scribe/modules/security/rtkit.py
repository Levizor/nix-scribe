import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

rtkit = Module("security.rtkit")


def _parse_exec_start_args(content: str) -> list[str]:
    """
    Simple parser to extract arguments from ExecStart line.
    """
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("ExecStart="):
            cmd_line = line.split("=", 1)[1]
            parts = cmd_line.split()
            if len(parts) > 1:
                return parts[1:]
    return []


@rtkit.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    exists = context.systemctl.exists("rtkit-daemon")

    if not exists:
        return {}

    ir = {"enable": True, "args": []}

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
                    ir["args"] = args
                break
            except Exception as e:
                logger.warning(f"Failed to read or parse {path}: {e}")

    return ir


@rtkit.mapper()
def map(ir: dict[str, Any]) -> SimpleOptionBlock | None:
    if not ir.get("enable"):
        return None

    data = {"enable": True}
    if ir.get("args"):
        data["args"] = ir["args"]

    return SimpleOptionBlock(
        name="rtkit",
        description="RealtimeKit system service",
        data={"security.rtkit": data},
    )
