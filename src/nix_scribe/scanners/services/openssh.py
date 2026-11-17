import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.openssh import parse_openssh_config
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.openssh import OpenSSH

logger = logging.getLogger(__name__)

openssh = Scanner("services.openssh")

SSHD_CONFIG_PATHS = [
    "/etc/ssh/sshd_config",
    "/etc/ssh/sshd_config.d",
]

SETTINGS_KEYS = {
    "PermitRootLogin",
    "PasswordAuthentication",
    "KbdInteractiveAuthentication",
    "ChallengeResponseAuthentication",
    "X11Forwarding",
    "Banner",
    "GatewayPorts",
    "LogLevel",
    "UseDns",
    "PrintMotd",
    "StrictModes",
}


def _infer_key_type(path: str) -> str:
    lower = path.lower()
    if "ed25519" in lower:
        return "ed25519"
    if "rsa" in lower:
        return "rsa"
    if "ecdsa" in lower:
        return "ecdsa"
    if "dsa" in lower:
        return "dsa"
    return "rsa"


@openssh.scanner()
def scan(context: SystemContext) -> OpenSSH | None:
    if not context.systemctl.is_enabled("sshd"):
        return None

    mod = OpenSSH(enable=True, ports=[])

    raw_config: dict[str, Any] = {}
    try:
        reader = ConfigReader(context, parse_openssh_config)
        raw_config = reader.read_merge_configs_from_paths_list(SSHD_CONFIG_PATHS)
    except Exception as e:
        logger.warning(f"Failed to read sshd configuration: {e}")

    if "Port" in raw_config:
        ports_raw = raw_config["Port"]
        if isinstance(ports_raw, list):
            mod.ports = [int(p) for p in ports_raw if str(p).isdigit()]
        elif str(ports_raw).isdigit():
            mod.ports = [int(ports_raw)]

    if "HostKey" in raw_config:
        keys_raw = raw_config["HostKey"]
        if not isinstance(keys_raw, list):
            keys_raw = [keys_raw]
        host_keys = []
        for key_path in keys_raw:
            if isinstance(key_path, str) and key_path.strip():
                p = key_path.strip()
                host_keys.append({"path": p, "type": _infer_key_type(p)})
        if host_keys:
            mod.hostKeys = host_keys

    settings: dict[str, Any] = {}
    for key, val in raw_config.items():
        if key in SETTINGS_KEYS:
            settings[key] = val

    if settings:
        mod.settings = settings

    return mod
