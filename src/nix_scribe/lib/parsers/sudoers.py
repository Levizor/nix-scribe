def parse_sudoers(content: str) -> dict[str, list[str]]:
    """
    Parses a sudoers configuration file content into lists of defaults, rules, and raw lines.
    """
    defaults: list[str] = []
    rules: list[str] = []
    raw_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        raw_lines.append(stripped)

        if stripped.startswith("Defaults"):
            defaults.append(stripped)
        else:
            rules.append(stripped)

    return {
        "defaults": defaults,
        "rules": rules,
        "raw_lines": raw_lines,
    }
