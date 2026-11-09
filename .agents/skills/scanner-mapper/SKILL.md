---
name: scanner-mapper
description: Guide and patterns for implementing nix-scribe reverse-engineering modules using declarative NixModule contracts and single-stage Scanners.
---

# NixModule & Scanner Architecture Guide

Every `nix-scribe` component pairs a declarative `NixModule` contract in `src/nix_scribe/modules/nixos/` with a single-stage filesystem `Scanner` in `src/nix_scribe/scanners/`.

## 1. Declarative `NixModule` Contract (`src/nix_scribe/modules/nixos/<category>/<name>.py`)

```python
from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option


class MyService(
    NixModule,
    prefix="services.myService",
    claims={"my-service"},
):
    """My Service NixOS Configuration"""

    enable: bool = option(default=False)
    settingName: str | None = option()
```

## 2. Single-Stage Scanner (`src/nix_scribe/scanners/<category>/<name>.py`)

```python
import logging

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.kv import parse_kv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.services.my_service import MyService

logger = logging.getLogger(__name__)

my_service = Scanner(
    "services.my_service",
    description="My Service NixOS Configuration",
)

CONFIG_PATH = "/etc/my_service/config.conf"


@my_service.scanner()
def scan(context: SystemContext) -> MyService | None:
    """
    100% Pure Filesystem Scanner.
    - Check file existence via context.path_exists()
    - Read files via context.read_file() or ConfigReader
    - Inspect directories via context.list_directory()
    - NEVER invoke shell commands or host binaries.
    """
    if not context.path_exists(CONFIG_PATH):
        return None

    reader = ConfigReader(context, parse_kv)
    config = reader.read_config(CONFIG_PATH)

    return MyService(
        enable=True,
        settingName=config.get("setting_name"),
    )
```

## Core Principles
1. **100% Pure Filesystem**: Read configuration files from the target root using `SystemContext`. Never run host binaries (`mount`, `systemctl`, `stat`).
2. **Parser Selection**:
   * Equals-delimited key-value (`KEY=VALUE`): `parse_kv`
   * Space-delimited key-value (`KEY VALUE`): `parse_space_kv`
   * INI files: `ConfigReader` with `parse_ini`
   * PAM files: `parse_pam`
   * Sudoers files: `parse_sudoers`
3. **NixOS Option Mapping**: Ensure `NixModule` field paths and defaults match NixOS options directly (verify via `nix eval`).
