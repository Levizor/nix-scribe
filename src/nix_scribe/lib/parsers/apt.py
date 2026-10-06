import re


def parse_deb822(content: str) -> list[dict[str, str]]:
    """Parses Debian 822 format (RFC 822 stanzas separated by blank lines)."""
    records: list[dict[str, str]] = []
    current_record: dict[str, str] = {}
    current_key: str | None = None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if current_record:
                records.append(current_record)
                current_record = {}
                current_key = None
            continue

        if line[0] in (" ", "\t"):
            if current_key and current_key in current_record:
                if stripped == ".":
                    current_record[current_key] += "\n"
                else:
                    current_record[current_key] += f"\n{stripped}"
        elif ":" in line:
            key, val = line.split(":", 1)
            current_key = key.strip()
            current_record[current_key] = val.strip()
        else:
            current_key = None

    if current_record:
        records.append(current_record)

    return records


def parse_extended_states(content: str) -> dict[str, dict[str, str]]:
    """Parses /var/lib/apt/extended_states, returning a mapping of package name to its state record."""
    records = parse_deb822(content)
    return {r["Package"]: r for r in records if "Package" in r}


def parse_dpkg_status(content: str) -> dict[str, dict[str, str]]:
    """Parses /var/lib/dpkg/status, returning a mapping of package name to its status record."""
    records = parse_deb822(content)
    return {r["Package"]: r for r in records if "Package" in r}


def parse_debian_relationship_packages(relation_text: str) -> list[str]:
    """Extracts package names from a Debian relationship field (Depends, Recommends)."""
    packages: list[str] = []
    for chunk in relation_text.split(","):
        for alt in chunk.split("|"):
            alt_clean = alt.strip()
            if not alt_clean:
                continue
            token = alt_clean.split()[0]
            if ":" in token:
                token = token.split(":", 1)[0]
            if token and re.match(r"^[a-zA-Z0-9][a-zA-Z0-9+.-]+$", token):
                packages.append(token)
    return packages
