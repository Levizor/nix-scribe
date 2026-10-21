import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.openssh import parse_openssh_config
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

openssh = Module("services.openssh")

SSHD_CONFIG_PATH = "/etc/ssh/sshd_config"
SSHD_CONFIG_DIR = "/etc/ssh/sshd_config.d"

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
def scan(context: SystemContext) -> dict[str, Any]:
    sshd_enabled = (
        context.systemctl.is_enabled("sshd")
        or context.path_exists(SSHD_CONFIG_PATH)
        or context.find_executable_path("sshd") is not None
    )

    ir: dict[str, Any] = {"enable": sshd_enabled}
    if not ir["enable"]:
        return ir

    paths = []
    if context.path_exists(SSHD_CONFIG_PATH):
        paths.append(SSHD_CONFIG_PATH)

    if context.path_exists(SSHD_CONFIG_DIR):
        dir_files = context.list_directory(SSHD_CONFIG_DIR)
        for fname in sorted(dir_files):
            if fname.endswith(".conf"):
                paths.append(f"{SSHD_CONFIG_DIR}/{fname}")

    raw_config: dict[str, Any] = {}
    if paths:
        try:
            reader = ConfigReader(context, parse_openssh_config)
            raw_config = reader.read_merge_configs_from_paths_list(paths)
        except Exception as e:
            logger.warning(f"Failed to read sshd configuration: {e}")

    # Extract ports
    if "Port" in raw_config:
        ports_raw = raw_config["Port"]
        if isinstance(ports_raw, list):
            ir["ports"] = [int(p) for p in ports_raw if str(p).isdigit()]
        elif str(ports_raw).isdigit():
            ir["ports"] = [int(ports_raw)]

    # Extract HostKeys
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
            ir["hostKeys"] = host_keys

    # Extract settings
    settings: dict[str, Any] = {}
    for key, val in raw_config.items():
        if key in SETTINGS_KEYS:
            settings[key] = val

    if settings:
        ir["settings"] = settings

    return ir


@openssh.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    config: dict[str, Any] = {"enable": True}

    if "ports" in ir and ir["ports"]:
        config["ports"] = ir["ports"]

    if "hostKeys" in ir and ir["hostKeys"]:
        config["hostKeys"] = ir["hostKeys"]

    if "settings" in ir and ir["settings"]:
        config["settings"] = ir["settings"]

    return ConfigFragment(
        name="openssh",
        description="OpenSSH Secure Shell Service",
        data={"services.openssh": config},
    )
