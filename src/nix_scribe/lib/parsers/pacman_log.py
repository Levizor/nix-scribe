from __future__ import annotations

import re
import shlex

PACMAN_RUNNING_PATTERN = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\]\s+\[PACMAN\]\s+Running\s+'(?P<cmdline>.*)'\s*$"
)
PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9@._+-]*$")
OPTIONS_WITH_ARG = {
    "-b",
    "-r",
    "--config",
    "--root",
    "--dbpath",
    "--cachedir",
    "--hookdir",
    "--logfile",
    "--gpgdir",
    "--color",
    "--arch",
    "--print-format",
    "--ignore",
    "--ignoregroup",
    "--overwrite",
    "--assume-installed",
    "--sysroot",
}
PKG_EXTENSIONS = (
    ".pkg.tar.zst",
    ".pkg.tar.xz",
    ".pkg.tar.gz",
    ".pkg.tar.bz2",
    ".pkg.tar.lrz",
    ".pkg.tar.lzo",
    ".pkg.tar.Z",
    ".pkg.tar",
)
WRAPPER_BINARIES = {"pacman", "yay", "paru", "pacstrap"}


def parse_pacman_log_cmdlines(content: str) -> list[tuple[str, str]]:
    """Extracts (timestamp, cmdline) tuples from pacman log entries."""
    cmdlines: list[tuple[str, str]] = []
    for line in content.splitlines():
        match = PACMAN_RUNNING_PATTERN.match(line.strip())
        if match:
            cmdlines.append((match.group("timestamp"), match.group("cmdline")))
    return cmdlines


def parse_pacman_cmdline(cmdline: str) -> tuple[str | None, set[str]]:
    """Parses a pacman command line into an action and target package names."""
    try:
        tokens = shlex.split(cmdline)
    except Exception:
        tokens = cmdline.split()
    if not tokens:
        return None, set()

    is_pacstrap = any("pacstrap" in t.lower() for t in tokens)
    is_bootstrap = is_pacstrap or any(
        t in ("-r", "--root", "--sysroot")
        or t.startswith(("-r/", "--root=", "--sysroot="))
        for t in tokens
    )

    while tokens and tokens[0] in ("sudo", "doas"):
        tokens.pop(0)
    if tokens and tokens[0].rsplit("/", 1)[-1] in WRAPPER_BINARIES:
        tokens.pop(0)

    operation = None
    as_deps = False
    as_explicit = False

    for tok in tokens:
        if tok.startswith("--"):
            long_opt = tok.split("=", 1)[0]
            if long_opt == "--sync":
                operation = "sync"
            elif long_opt == "--upgrade":
                operation = "upgrade"
            elif long_opt == "--remove":
                operation = "remove"
            elif long_opt == "--database":
                operation = "database"
            elif long_opt == "--asdeps":
                as_deps = True
            elif long_opt == "--asexplicit":
                as_explicit = True
        elif tok.startswith("-") and len(tok) > 1:
            flags = tok[1:]
            if "S" in flags:
                operation = "sync"
            elif "R" in flags:
                operation = "remove"
            elif "U" in flags:
                operation = "upgrade"
            elif "D" in flags:
                operation = "database"
            elif "Q" in flags:
                operation = "query"
            elif "F" in flags:
                operation = "files"

    if is_bootstrap:
        action = "bootstrap"
    elif operation in ("sync", "upgrade"):
        action = "asdeps" if as_deps else "install"
    elif operation == "remove":
        action = "remove"
    elif operation == "database":
        if as_explicit:
            action = "install"
        elif as_deps:
            action = "asdeps"
        else:
            action = None
    else:
        action = None

    packages: set[str] = set()
    skip_next = False
    skipped_pacstrap_root = not is_pacstrap
    for tok in tokens:
        if skip_next:
            skip_next = False
            continue
        if tok in OPTIONS_WITH_ARG:
            skip_next = True
            continue
        if tok.startswith("-"):
            continue
        if not skipped_pacstrap_root:
            skipped_pacstrap_root = True
            continue

        target = tok
        if any(target.endswith(ext) for ext in PKG_EXTENSIONS):
            base = target.split("/")[-1]
            for ext in PKG_EXTENSIONS:
                if base.endswith(ext):
                    base = base[: -len(ext)]
                    break
            parts = base.rsplit("-", 3)
            if len(parts) == 4:
                target = parts[0]
        elif "/" in target:
            target = target.rsplit("/", 1)[-1]

        target = re.split(r"[><=]", target, maxsplit=1)[0]
        if PACKAGE_NAME_PATTERN.match(target):
            packages.add(target)

    return action, packages


def extract_explicit_packages_from_log(content: str) -> set[str]:
    """Replays command lines from pacman log content to compute active explicit packages."""
    explicit_packages: set[str] = set()
    for _, cmdline in parse_pacman_log_cmdlines(content):
        action, packages = parse_pacman_cmdline(cmdline)
        if action == "install":
            explicit_packages.update(packages)
        elif action in ("remove", "asdeps"):
            explicit_packages.difference_update(packages)
    return explicit_packages
