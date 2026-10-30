import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.openssh import parse_openssh_config
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

ssh = Module("programs.ssh")

SSH_CONFIG_PATHS = [
    "/etc/ssh/ssh_config",
    "/etc/ssh/ssh_config.d",
]

KNOWN_CLIENT_DIRECTIVES = {
    "ForwardX11",
    "ForwardAgent",
    "AddKeysToAgent",
}


@ssh.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ssh_enabled = context.find_executable_path("ssh") is not None or any(
        context.path_exists(p) for p in SSH_CONFIG_PATHS
    )

    if not ssh_enabled:
        return {}

    ir: dict[str, Any] = {"enable": True}

    raw_config: dict[str, Any] = {}
    try:
        reader = ConfigReader(context, parse_openssh_config)
        raw_config = reader.read_merge_configs_from_paths_list(SSH_CONFIG_PATHS)
    except Exception as e:
        logger.warning(f"Failed to read ssh configuration: {e}")

    if "ForwardX11" in raw_config:
        ir["forwardX11"] = bool(raw_config["ForwardX11"])

    agent_active = (
        context.systemctl.is_enabled("ssh-agent")
        or context.systemctl.is_enabled("ssh-agent.socket")
        or str(raw_config.get("AddKeysToAgent", "")).lower()
        in ("yes", "true", "confirm", "1")
    )
    if agent_active:
        ir["startAgent"] = True

    extra_lines = []
    for key, val in raw_config.items():
        if key not in KNOWN_CLIENT_DIRECTIVES:
            if isinstance(val, list):
                for item in val:
                    extra_lines.append(f"{key} {item}")
            else:
                extra_lines.append(f"{key} {val}")

    if extra_lines:
        ir["extraConfig"] = "\n".join(extra_lines)

    return ir


@ssh.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    config: dict[str, Any] = {}

    if "forwardX11" in ir:
        config["forwardX11"] = ir["forwardX11"]

    if ir.get("startAgent"):
        config["startAgent"] = True

    if "extraConfig" in ir and ir["extraConfig"]:
        config["extraConfig"] = ir["extraConfig"]

    return ConfigFragment(
        name="ssh",
        description="OpenSSH Client Configuration",
        data={"programs.ssh": config},
        claims={"openssh"},
    )
