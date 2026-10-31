import re
from typing import Any

SECTION_HEADER_PATTERN = re.compile(r"^%([A-Z0-9_-]+)%$")

LIST_TAGS = {
    "DEPENDS",
    "OPTDEPENDS",
    "PROVIDES",
    "CONFLICTS",
    "REPLACES",
    "GROUPS",
    "LICENSE",
    "BACKUP",
    "MAKEDEPENDS",
    "CHECKDEPENDS",
}


def parse_pacman_desc(content: str) -> dict[str, Any]:
    """Parses an ALPM pacman desc file into a dictionary of tags and values."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_key is None:
            return
        if current_key in LIST_TAGS:
            result[current_key] = list(current_lines)
        else:
            if not current_lines:
                result[current_key] = ""
            elif len(current_lines) == 1:
                result[current_key] = current_lines[0]
            else:
                result[current_key] = current_lines

    for line in content.splitlines():
        match = SECTION_HEADER_PATTERN.match(line.strip())
        if match:
            flush()
            current_key = match.group(1)
            current_lines = []
        elif current_key is not None:
            stripped = line.strip()
            if stripped:
                current_lines.append(stripped)

    flush()
    return result
