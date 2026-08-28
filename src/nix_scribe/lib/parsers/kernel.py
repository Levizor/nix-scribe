from typing import Any


def parse_modules(content: str) -> dict[str, Any]:
    """
    Parses /etc/modules and /etc/modules-load.d/*.conf lines into a dictionary.
    Returns {"modules": ["mod1", "mod2", ...]}.
    """
    modules = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ";")):
            parts = line.split()
            if parts:
                modules.append(parts[0])
    return {"modules": modules}


def parse_modprobe(content: str) -> dict[str, Any]:
    """
    Parses /etc/modprobe.d/*.conf lines into blacklisted modules and extra modprobe configs.
    Returns {"blacklisted": [...], "extra": [...]}.
    """
    blacklisted = []
    extra = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[0] == "blacklist":
            blacklisted.append(parts[1])
        elif (
            len(parts) >= 3
            and parts[0] == "install"
            and parts[2] in ("/bin/true", "/bin/false", "/bin/disabled")
        ):
            blacklisted.append(parts[1])
        else:
            extra.append(stripped)

    return {"blacklisted": blacklisted, "extra": extra}
