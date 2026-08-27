# nix-scribe - Agent Instructions

This document defines the core patterns and standards for `nix-scribe`. Adhere to these strictly to ensure consistency and quality.

## Implementation Standards
- **Minimal Comments**: Do not write comments for obvious code. Write concise docstrings only for complex functions where the name is not self-explanatory.
- **Type Safety**: Use type hints for all function signatures and complex variables. Use modern lowercase types for collections (e.g., `list[str]`, `dict[str, Any]`) instead of importing from `typing` (e.g., `List`, `Dict`).
- **Scanner/Mapper Pattern**: Every module must follow the `BaseScanner` and `BaseMapper` architecture.
    - **Scanner**: Performs 100% pure filesystem-based scanning using `context.path_exists()`, `context.read_file()`, and `context.list_directory()`. **Never** invoke host binaries (`mount`, `systemctl`, `stat`) inside scanner functions. Returns an IR (Intermediate Representation).
    - **Mapper**: Transforms IR into `ConfigFragment` / `OptionBlock`.
- **System Context**: `SystemContext._run_command` is private and reserved strictly for internal privileged file fallback (`sudo cat`, `sudo ls`). Modules must never call shell execution functions.
- **Deep Merging**: Use the `deepmerge` library (specifically `always_merger`) when merging configurations in `ConfigReader`.
- **Directory Detection**: Use `os.path.isdir()` in `ConfigReader` to maintain compatibility with `unittest.mock` and ensure reliable directory detection in real systems.

## NixOS Options Discovery
- **Authoritative Options Querying**: To discover or verify NixOS option names, types, and defaults, evaluate `nixpkgs` directly:
  `nix eval --json --impure --expr 'let eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; }; in builtins.attrNames eval.options.<attribute.path>'`
  For dynamic option sets (e.g. `services.<name>`, `luks.devices.<name>`):
  `nix eval --json --impure --expr 'let eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; }; in builtins.attrNames (eval.options.<path>.type.getSubOptions [])'`

## Testing Standards
- **Filesystem-backed Tests**: Use `pytest`'s `tmp_path` fixture for all module and parser tests.
    - Do **not** use complex, nested `unittest.mock` calls to simulate the filesystem.
    - Manually create the required directory structure and files within `tmp_path`.
    - Pass the `tmp_path` to `SystemContext(root=tmp_path)`.
- **Mocking Strategy**: Only mock non-filesystem interactions such as:
    - `systemctl` status (`context.systemctl.is_enabled`).
    - External command execution (`context.run_command`).
    - Binary discovery (`context.find_executable_path`).
- **Integration Tests**: Use the existing `tests/systems/generic` root for full-system integration verification.

## Git & Workflow
- **Commit Messages**: Prefer concise, lowercase messages (e.g., `fix: ...`, `feat: ...`, `mod: ...`). Focus on the "what" and "why".
- **Tooling**: Always use `ruff check --fix` and `ruff format` before finalizing changes. Use `uv run pytest` to ensure all tests pass in the correct environment.
- **Proactiveness**: If a bug is found in core libraries (like `ConfigReader`) during module development, fix it at the source rather than working around it in the module.

## Directory Structure
- `src/nix_scribe/modules/`: Module definitions organized by category.
- `src/nix_scribe/lib/`: Core logic, parsers, and writer.
- `tests/modules/`: Unit tests for individual modules using `tmp_path`.
- `tests/systems/`: Static system roots for integration testing.
