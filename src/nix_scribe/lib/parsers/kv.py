import re
from typing import Any


def parse_kv(content: str) -> dict[str, Any]:
    """
    Parses a simple key-value configuration file (e.g., /etc/default/grub).
    Supports shell-style assignments: KEY=VALUE or KEY="VALUE"
    """
    result = {}
    pattern = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$")

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
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
