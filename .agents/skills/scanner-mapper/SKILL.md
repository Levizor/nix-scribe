---
name: scanner-mapper
description: Guide and patterns for implementing nix-scribe reverse-engineering modules using pure filesystem Scanner and Mapper functions.
---

# Scanner / Mapper Module Architecture Guide

Every `nix-scribe` module inspects a component of the target host system and outputs declarative NixOS configuration blocks.

## Module Structure Template

```python
import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.kv import parse_kv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

my_module = Module("category.name")


@my_module.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    """
    100% Pure Filesystem Scanner.
    - Check file existence via context.path_exists()
    - Read files via context.read_file() or ConfigReader
    - Inspect directories via context.list_directory()
    - NEVER invoke shell commands or host binaries.
    """
    if not context.path_exists("/etc/my_service/config.conf"):
        return {}

    reader = ConfigReader(context, parse_kv)
    config = reader.read_config("/etc/my_service/config.conf")

    return {
        "enable": True,
        "settingName": config.get("setting_name"),
    }


@my_module.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    """
    Transforms IR into NixOS ConfigFragment.
    - Returns None if disabled or empty.
    - Returns ConfigFragment with NixOS option mappings.
    """
    if not ir or not ir.get("enable"):
        return None

    config: dict[str, Any] = {"enable": True}

    if "settingName" in ir:
        config["settingName"] = ir["settingName"]

    return ConfigFragment(
        name="my-service",
        description="My Service NixOS Configuration",
        data={"services.myService": config},
    )
```

## Core Principles
1. **100% Pure Filesystem**: Read configuration files from the target root using `SystemContext`. Never run host binaries (`mount`, `systemctl`, `stat`).
2. **Parser Selection**:
   * Equals-delimited key-value (`KEY=VALUE`): `parse_kv`
   * Space-delimited key-value (`KEY VALUE`): `parse_space_kv`
   * INI files: `ConfigReader` with standard INI parser
   * PAM files: `parse_pam`
   * Sudoers files: `parse_sudoers`
3. **NixOS Option Mapping**: Ensure option names match NixOS options directly (verify via `nix eval`).
