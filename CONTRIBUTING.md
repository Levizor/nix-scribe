# Contributing

Contributions are welcome! While there are no strict rules regarding how to write the code yet, please strive to follow good programming practices and maintain consistency with the existing codebase.

## How to Add a Module

To add a module, find (or create) the appropriate directory in `src/nix_scribe/modules/` and create a file for its definition. For example, to add a module for `vim`, you would create `vim.py` in the `src/nix_scribe/modules/programs/` directory.

Each module file must instantiate a `Module` class assigned to a `module` variable, containing a **Scanner** and a **Mapper**.

### Example Module
Here is how a simple module looks (using Hyprland as an example):

```python
# src/nix_scribe/modules/programs/hyprland.py

from typing import Any
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

class HyprlandScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        # just check if Hyprland binary exists on the target system
        return {"enable": bool(context.find_executable_path("Hyprland"))}

class HyprlandMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        # nothing to return if there's no Hyprland
        if not ir.get("enable"):
            return None

        return SimpleOptionBlock(
            name="programs/hyprland",
            description="Hyprland compositor",
            data={"programs.hyprland.enable": True},
        )

module = Module("hyprland", HyprlandScanner(), HyprlandMapper())
```

---

## Architecture Overview

Essentially, nix-scribe is a lightweight framework providing abstraction for reading the state and replicating it with nixos options. The starting point is located at [src/nix_scribe/nixscribe.py](./src/nix_scribe/nixscribe.py).

The flow is divided in 4 stages:
1. Collecting modules defined in [src/nix_scribe/modules](./src/nix_scribe/modules).
2. Running a Scan for all the modules
3. Mapping all the collected data into option blocks
4. Writing it all down into .nix files

### The Scanner
The **Scanner** is responsible for fetching data from the system and parsing it into an **Intermediate Representation (IR)**, which is then used by the Mapper. How to define IR in your modules is up to you.

* **Filesystem-based Scanning:** In `nix-scribe`, all scanning should ideally be done in a filesystem-based way. This means the script should avoid running shell commands to read state whenever possible.
* **Implementation:** Any class inheriting from `BaseScanner` must define a `scan(self, context: SystemContext)` method.

### SystemContext
`SystemContext` is the primary interface for communicating with the target system. It provides high-level methods to:
* Search for executables (`find_executable_path`).
* Read systemd services status.
* Read files and list directories (handling permissions/sudo automatically).
* Check path existence.

### The Mapper
The **Mapper**'s responsibility is to process the IR produced by the Scanner to build and return an **OptionBlock**.

### Option Block
An `OptionBlock` is a Pythonic representation of a Nix configuration set. These blocks are processed by the engine and written into the final NixOS configuration files.

An Option Block typically consists of:
1. **Name**: Identifier for the block (may be used in debugging)
2. **Description**: May be used as a comment in the generated Nix file.
3. **Arguments set**: Set of arguments required by the block (e.g., `pkgs`, `lib`, `config`). These are added to the function parameters in the resulting Nix code.
4. **Assets set**: Files that need to be copied from the target system into the Nix configuration (e.g., wallpapers, specific config files).

#### SimpleOptionBlock
For most modules, `SimpleOptionBlock` is the preferred choice. It provides a `data: dict` parameter and implements the render() method. It also handles the detection of arguments and assets to minimize frictio[.](2026-02-27_..md).

**Example:**
```python
SimpleOptionBlock(
    name="networkmanager",
    description="NetworkManager configuration",
    data={
        "networking.networkmanager": {
            "enable": True,
            "plugins": [raw("pkgs.networkmanager-openvpn")],
        }
    },
    arguments=["pkgs"]
)
```

**Generates:**
```nix
# NetworkManager configuration
networking.networkmanager = {
  enable = true;
  plugins = [
    pkgs.networkmanager-openvpn
  ];
};
```

#### Custom Option Blocks
You can create your own option blocks by inheriting from `BaseOptionBlock` and overriding the `render()` method if you want to achieve some specific format of the resulting configuration, though this is probably unnecessary.

---

## Development Workflow

### flake and direnv
Nix flake provides a development shell:
```bash
nix develop
```

You can use direnv to automatically apply it upon entering the directory:
```
direnv allow
```

### Testing
When adding a new module, it's a good idea to include corresponding tests in the `tests/modules/` directory to ensure reliability.

To run the tests:
```bash
pytest
```

### Code Quality
Use **ruff** for linting and formatting.

```bash
ruff check --fix
ruff format
```

### Type Hints
The project uses type hints extensively. Please provide type annotations for all function signatures and complex variables to keep the codebase maintainable and readable.
