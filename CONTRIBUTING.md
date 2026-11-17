# Contributing

Contributions are welcome! While there are no strict rules regarding how to write the code yet, please strive to follow good programming practices and maintain consistency with the existing codebase.

## How to Add a Module

A module in `nix-scribe` consists of two parts:
1. **Declarative Contract (`NixModule`)**: Lives in `src/nix_scribe/modules/nixos/<category>/<name>.py`. Defines the schema and options matching NixOS options directly.
2. **Scanner (`Scanner`)**: Lives in `src/nix_scribe/scanners/<category>/<name>.py`. Pure filesystem inspection that populates the declarative contract.

### Example Contract & Scanner

```python
# src/nix_scribe/modules/nixos/programs/hyprland.py

from nix_scribe.lib.nix_module import NixModule, option


class Hyprland(NixModule, prefix="programs.hyprland", claims={"hyprland"}):
    """Hyprland compositor configuration"""

    enable: bool = option()
```

```python
# src/nix_scribe/scanners/programs/hyprland.py

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.programs.hyprland import Hyprland

hyprland = Scanner("programs.hyprland")


@hyprland.scanner()
def scan(context: SystemContext) -> Hyprland | None:
    if not context.find_executable_path("Hyprland"):
        return None

    return Hyprland(enable=True)
```

---

## Architecture Overview

`nix-scribe` scans system state and generates corresponding NixOS configuration. The entry point is in [src/nix_scribe/nixscribe.py](./src/nix_scribe/nixscribe.py).

The execution flow:
1. **Module Discovery**: `ScannerLoader` imports all scanners from `src/nix_scribe/scanners/` and any external plugins passed via `--plugin`.
2. **Scheduling**: `ScannerScheduler` sorts active scanners by `ScannerPhase` (`EARLY`, `NORMAL`, `LATE`) and name.
3. **Scanning**: Scanners inspect the target filesystem through `SystemContext` and return populated `NixModule` contract instances or `None`.
4. **Assembly & Writing**: `NixFile` and `NixWriter` format active options into `.nix` files based on the requested modularization level.

### The Scanner & SystemContext

Scanners collect state from the target system and return populated `NixModule` instances.

- **Filesystem-only scanning**: Never invoke host shell binaries (`mount`, `systemctl`, `stat`). Read files and directories via `context.path_exists()`, `context.read_file()`, `context.read_file_bytes()`, `context.list_directory()`, and `context.find_executable_path()`. This keeps scanning safe on mounted offline root directories.
- **Path constants**: Define paths at the top of the scanner file (e.g. `CONFIG_PATH = "/etc/example.conf"`).
- **Reusable parsers**: Place parse functions in `src/nix_scribe/lib/parsers/<name>.py`.
- **Merged configs**: When configs are split across files and drop-in directories (like `/etc/sudoers` and `/etc/sudoers.d/`), instantiate `ConfigReader(context, parse_func)` and call `read_merge_configs_from_paths_list([FILE_PATH, DIR_PATH])`. It automatically reads all files and handles merging internally.

### Declarative Contracts (`NixModule`)

- **Option Definitions**: Declare options via `option(...)` with their natural Python types (`enable: bool = option()`, `port: int = option()`, `servers: list[str] = option()`).
- **Never use `| None` in option typehints**: All options are presence-driven and implicitly default to unconfigured (`None` for scalars, empty collection factories for lists/dicts/sets).
- **Package Claiming**: Declare claimed packages statically on `NixModule(..., claims={"pkg"})`, on individual options `option(..., claims={"pkg"})`, or dynamically via `mod.claim("pkg")`. Claimed packages are automatically excluded from `environment.systemPackages`.

### Execution Phases

Scanners can set an execution phase when instantiated:
- `ScannerPhase.EARLY` (10): Runs before standard scanners.
- `ScannerPhase.NORMAL` (50): Default. Standard scanners run here.
- `ScannerPhase.LATE` (100): Runs after standard scanners. Used by aggregators like `environment.system_packages` to collect unclaimed packages after all earlier scanners have executed.

```python
system_packages = Scanner("environment.system_packages", phase=ScannerPhase.LATE)
```
        "networking.networkmanager.plugins": [raw("pkgs.networkmanager-openvpn")],
    },
)
```

Values can use helper types:
- `raw("pkgs.foo")`: Emits raw Nix identifiers.
- `comment("text")`: Emits comments within list structures.
- `Asset(target_filename, content)`: Writes in-memory file assets (like wallpapers, certificates, or logs) into the generated config directory.

---

## Development Workflow

### Development Shell

Use the Nix development shell:
```bash
nix develop
```

Or enable `direnv`:
```bash
direnv allow
```

### Testing

Write unit tests using pytest's `tmp_path` fixture:
- Create simulated filesystem files and directories in `tmp_path`.
- Pass `tmp_path` to `SystemContext(root=tmp_path)`.
- Do not use complex nested `unittest.mock` calls for filesystem operations.
- Mock only non-filesystem operations (`context.find_executable_path`, `context.systemctl`).

Run tests:
```bash
direnv exec . pytest
```

### Linting and Formatting

Run `ruff` before committing:
```bash
direnv exec . ruff check --fix
direnv exec . ruff format
```

### Type Hints

Use standard lowercase types for type hints (`list[str]`, `dict[str, Any]`, `tuple[int, ...]`) instead of importing `List` or `Dict` from `typing`. Provide type hints on all public functions.
