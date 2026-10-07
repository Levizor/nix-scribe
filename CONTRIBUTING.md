# Contributing

Contributions are welcome! While there are no strict rules regarding how to write the code yet, please strive to follow good programming practices and maintain consistency with the existing codebase.

## How to Add a Module

Create a file inside `src/nix_scribe/modules/<category>/`. For example, a module for `git` lives in `src/nix_scribe/modules/programs/git.py`. The category generally should follow the NixOs option the module defines.

A module instantiates `Module`, defines a scanner with `@<mod>.scanner()`, and defines a mapper with `@<mod>.mapper()`.

### Example Module

```python
# src/nix_scribe/modules/programs/hyprland.py

from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

hyprland = Module("programs.hyprland")


@hyprland.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    # Check if binary exists on target filesystem
    return {"enable": bool(context.find_executable_path("Hyprland"))}


@hyprland.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="hyprland",
        description="Hyprland compositor",
        data={"programs.hyprland.enable": True},
    )
```

---

## Architecture Overview

`nix-scribe` scans system state and generates corresponding NixOS configuration. The entry point is in [src/nix_scribe/nixscribe.py](./src/nix_scribe/nixscribe.py).

The execution flow:
1. **Module Discovery**: `ModuleLoader` imports all modules from `src/nix_scribe/modules/` and any external plugins passed via `--plugin`.
2. **Scheduling**: `ModuleScheduler` sorts active modules by `ModulePhase` (`EARLY`, `NORMAL`, `LATE`) and name.
3. **Scanning**: Scanners inspect the target filesystem through `SystemContext` and return an Intermediate Representation (IR) dict.
4. **Mapping**: Mappers convert IR dicts into `ConfigFragment` instances.
5. **Assembly & Writing**: `NixFile` and `NixWriter` format options into `.nix` files based on the requested modularization level.

### The Scanner & SystemContext

Scanners collect state from the target system into an IR dictionary.

- **Filesystem-only scanning**: Never invoke host shell binaries (`mount`, `systemctl`, `stat`). Read files and directories via `context.path_exists()`, `context.read_file()`, `context.list_directory()`, and `context.find_executable_path()`. This keeps scanning safe on mounted offline root directories.
- **Path constants**: Define paths at the top of the module file (e.g. `CONFIG_PATH = "/etc/example.conf"`).
- **Reusable parsers**: Place parse functions in `src/nix_scribe/lib/parsers/<name>.py`.
- **Merged configs**: When configs are split across files and drop-in directories (like `/etc/sudoers` and `/etc/sudoers.d/`), instantiate `ConfigReader(context, parse_func)` and call `read_merge_configs_from_paths_list([FILE_PATH, DIR_PATH])`. It automatically reads all files and handles merging internally.

### Package Managers & Package Claiming

`nix-scribe` detects installed packages on the target system (e.g. Debian/Ubuntu APT) through `PackageManager` implementations.

- **Package State**: Access discovered packages via `context.packages`.
- **Declarative Package Claiming**: If your module configures a package (for example, `programs.git` configuring git), declare it in the returned `ConfigFragment`:
  ```python
  ConfigFragment(
      name="git",
      data={"programs.git.enable": True},
      claims={"git"},
  )
  ```
  During the mapping phase, `NixScribe` marks claimed packages in `context.packages`.
- **Unclaimed Packages**: Modules running in `ModulePhase.LATE` (specifically `environment.system_packages`) inspect `context.packages.unclaimed` at map time and emit all remaining user-installed packages into `environment.systemPackages`. Claiming prevents duplicate package definitions. If a module returns `None`, it claims nothing, and the package safely stays in `systemPackages`.

To add support for another package manager (like pacman or dnf):
1. Subclass `PackageManager` in `src/nix_scribe/lib/packages/managers/<name>.py`.
2. Implement `detect(context)` and `discover_packages(context)`.
3. Register it with `register_package_manager(YourManager)`.

### Execution Phases

Modules can set an execution phase when instantiated:
- `ModulePhase.EARLY` (10): Runs before standard modules.
- `ModulePhase.NORMAL` (50): Default. Standard modules run here and emit fragments.
- `ModulePhase.LATE` (100): Runs after standard modules. Used by `environment.system_packages` to collect unclaimed packages after all earlier modules have mapped.

```python
system_packages = Module("environment.system_packages", phase=ModulePhase.LATE)
```

### The Mapper & ConfigFragment

Mappers take the IR dictionary and return a `ConfigFragment` or `None`.

```python
from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.option_block import ConfigFragment

ConfigFragment(
    name="networkmanager",
    description="NetworkManager configuration",
    claims={"networkmanager"},
    data={
        "networking.networkmanager.enable": True,
        "networking.networkmanager.plugins": [raw("pkgs.networkmanager-openvpn")],
    },
)
```

Values can use helper types:
- `raw("pkgs.foo")`: Emits raw Nix identifiers.
- `comment("text")`: Emits comments within list structures.
- `nix_with("pkgs", [...])` or `with_pkgs(...)`: Wraps lists in `with <scope>;`.
- `Asset(source_path, target_filename)`: Copies external files (like wallpapers or certificates) into the generated config directory.

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
