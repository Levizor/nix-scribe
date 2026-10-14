import re
from dataclasses import dataclass, field

PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9+.-]+$")
PACKAGE_RECORD_PATTERN = re.compile(
    r"([a-zA-Z0-9][a-zA-Z0-9+.-]*(?::[a-zA-Z0-9_-]+)?)\s*\(([^)]*)\)"
)


@dataclass(frozen=True)
class AptHistoryPackage:
    name: str
    version: str = ""
    architecture: str | None = None
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class AptHistoryRecord:
    start_date: str | None = None
    commandline: str | None = None
    install: list[AptHistoryPackage] = field(default_factory=list)
    upgrade: list[AptHistoryPackage] = field(default_factory=list)
    remove: list[AptHistoryPackage] = field(default_factory=list)
    purge: list[AptHistoryPackage] = field(default_factory=list)
    reinstall: list[AptHistoryPackage] = field(default_factory=list)
    end_date: str | None = None


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
            if token and PACKAGE_NAME_PATTERN.match(token):
                packages.append(token)
    return packages


def parse_apt_history_packages(text: str) -> list[AptHistoryPackage]:
    packages: list[AptHistoryPackage] = []
    for match in PACKAGE_RECORD_PATTERN.finditer(text):
        pkg_token, details = match.groups()
        if ":" in pkg_token:
            name, arch = pkg_token.split(":", 1)
        else:
            name, arch = pkg_token, None
        parts = [p.strip() for p in details.split(",")]
        version = parts[0] if parts else ""
        flags = tuple(parts[1:]) if len(parts) > 1 else ()
        packages.append(
            AptHistoryPackage(
                name=name,
                version=version,
                architecture=arch,
                flags=flags,
            )
        )
    return packages


def parse_apt_history(content: str) -> list[AptHistoryRecord]:
    """Parses Debian 822 format /var/log/apt/history.log into transaction records."""
    records = parse_deb822(content)
    history: list[AptHistoryRecord] = []

    for record in records:
        history.append(
            AptHistoryRecord(
                start_date=record.get("Start-Date"),
                commandline=record.get("Commandline"),
                install=(
                    parse_apt_history_packages(record["Install"])
                    if "Install" in record
                    else []
                ),
                upgrade=(
                    parse_apt_history_packages(record["Upgrade"])
                    if "Upgrade" in record
                    else []
                ),
                remove=(
                    parse_apt_history_packages(record["Remove"])
                    if "Remove" in record
                    else []
                ),
                purge=(
                    parse_apt_history_packages(record["Purge"])
                    if "Purge" in record
                    else []
                ),
                reinstall=(
                    parse_apt_history_packages(record["Reinstall"])
                    if "Reinstall" in record
                    else []
                ),
                end_date=record.get("End-Date"),
            )
        )

    return history
