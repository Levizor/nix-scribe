import re
from typing import Any

BOOL_DIRECTIVES = {
    "passwordauthentication",
    "kbdinteractiveauthentication",
    "challengeresponseauthentication",
    "x11forwarding",
    "usedns",
    "printmotd",
    "strictmodes",
    "pubkeyauthentication",
    "allowagentforwarding",
    "allowtcpforwarding",
    "forwardx11",
    "forwardagent",
}

INT_DIRECTIVES = {
    "port",
    "clientaliveinterval",
    "clientalivecountmax",
    "serveraliveinterval",
    "serveralivecountmax",
}

LIST_DIRECTIVES = {
    "port",
    "hostkey",
    "authorizedkeysfile",
    "allowusers",
    "allowgroups",
    "denyusers",
    "denygroups",
    "ciphers",
    "macs",
    "kexalgorithms",
}

CANONICAL_KEYS = {
    "port": "Port",
    "permitrootlogin": "PermitRootLogin",
    "passwordauthentication": "PasswordAuthentication",
    "kbdinteractiveauthentication": "KbdInteractiveAuthentication",
    "challengeresponseauthentication": "ChallengeResponseAuthentication",
    "x11forwarding": "X11Forwarding",
    "banner": "Banner",
    "gatewayports": "GatewayPorts",
    "loglevel": "LogLevel",
    "usedns": "UseDns",
    "printmotd": "PrintMotd",
    "strictmodes": "StrictModes",
    "hostkey": "HostKey",
    "authorizedkeysfile": "AuthorizedKeysFile",
    "allowusers": "AllowUsers",
    "allowgroups": "AllowGroups",
    "denyusers": "DenyUsers",
    "denygroups": "DenyGroups",
    "ciphers": "Ciphers",
    "macs": "Macs",
    "kexalgorithms": "KexAlgorithms",
    "forwardx11": "ForwardX11",
    "forwardagent": "ForwardAgent",
    "addkeystoagent": "AddKeysToAgent",
}


def _parse_value(directive_lower: str, raw_val: str) -> Any:
    val = raw_val.strip()
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        val = val[1:-1].strip()

    val_lower = val.lower()

    if directive_lower in BOOL_DIRECTIVES:
        if val_lower in ("yes", "true", "1", "on"):
            return True
        if val_lower in ("no", "false", "0", "off"):
            return False

    if directive_lower == "permitrootlogin":
        if val_lower in ("yes", "true", "1"):
            return True
        if val_lower in ("no", "false", "0"):
            return False
        return val

    if directive_lower in INT_DIRECTIVES:
        try:
            return int(val)
        except ValueError:
            return val

    return val


def parse_openssh_config(content: str) -> dict[str, Any]:
    """
    Parses OpenSSH sshd_config or ssh_config text into a dictionary of directive keys and values.
    """
    result: dict[str, Any] = {}
    directive_re = re.compile(r"^\s*([A-Za-z0-9_@.-]+)(?:[\s=]+(.*))?$")

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(";"):
            continue

        match = directive_re.match(stripped)
        if not match:
            continue

        key_raw, val_raw = match.group(1), match.group(2) or ""
        dir_lower = key_raw.lower()
        key_canonical = CANONICAL_KEYS.get(dir_lower, key_raw)
        parsed_val = _parse_value(dir_lower, val_raw)

        if dir_lower in LIST_DIRECTIVES:
            if key_canonical not in result:
                result[key_canonical] = []
            elif not isinstance(result[key_canonical], list):
                result[key_canonical] = [result[key_canonical]]

            if isinstance(parsed_val, list):
                result[key_canonical].extend(parsed_val)
            else:
                result[key_canonical].append(parsed_val)
        else:
            result[key_canonical] = parsed_val

    return result
