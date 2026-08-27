from typing import Any


def parse_pam(content: str) -> dict[str, Any]:
    """
    Parses a PAM service configuration file content.
    Returns parsed rules, detected module flags, and raw lines.
    """
    rules: list[dict[str, Any]] = []
    has_ssh_agent_auth = False
    has_u2f = False
    has_yubico = False
    has_mount = False
    has_kwallet = False
    has_gnupg = False
    has_howdy = False
    has_google_authenticator = False
    has_duo = False
    raw_lines: list[str] = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        raw_lines.append(line)
        parts = line.split()
        if len(parts) >= 3:
            rule_type, control, module = parts[0], parts[1], parts[2]
            args = parts[3:] if len(parts) > 3 else []
            rules.append(
                {
                    "type": rule_type,
                    "control": control,
                    "module": module,
                    "args": args,
                    "raw": line,
                }
            )
            if "pam_ssh_agent_auth" in module:
                has_ssh_agent_auth = True
            if "pam_u2f" in module:
                has_u2f = True
            if "pam_yubico" in module:
                has_yubico = True
            if "pam_mount" in module:
                has_mount = True
            if "pam_kwallet" in module:
                has_kwallet = True
            if "pam_gnupg" in module:
                has_gnupg = True
            if "pam_howdy" in module:
                has_howdy = True
            if "pam_google_authenticator" in module:
                has_google_authenticator = True
            if "pam_duo" in module:
                has_duo = True

    return {
        "rules": rules,
        "has_ssh_agent_auth": has_ssh_agent_auth,
        "has_u2f": has_u2f,
        "has_yubico": has_yubico,
        "has_mount": has_mount,
        "has_kwallet": has_kwallet,
        "has_gnupg": has_gnupg,
        "has_howdy": has_howdy,
        "has_google_authenticator": has_google_authenticator,
        "has_duo": has_duo,
        "raw_lines": raw_lines,
    }
