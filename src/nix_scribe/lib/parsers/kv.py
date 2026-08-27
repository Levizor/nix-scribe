import re
from typing import Any


def parse_kv(content: str) -> dict[str, Any]:
    """
    Parses a simple key-value configuration file (e.g., /etc/default/grub).
    Supports shell-style assignments: KEY=VALUE or KEY="VALUE"
    """
    result = {}
    pattern = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=\s*(.*)\s*$")

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        match = pattern.match(line)
        if match:
            key = match.group(1)
            value = match.group(2)
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]

            result[key] = value

    return result


def is_truthy(value: Any) -> bool:
    """
    Returns True if value represents a truthy config state (e.g. True, 1, "1", "true", "yes", "on").
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.lower().strip() in ("1", "true", "yes", "on")
    return False


def parse_space_kv(content: str) -> dict[str, Any]:
    """
    Parses whitespace-delimited key-value configuration files (e.g., systemd-boot loader.conf).
    """
    result: dict[str, Any] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        parts = line.split(None, 1)
        if len(parts) == 2:
            key = parts[0].strip()
            value = parts[1].strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key] = value

    return result
