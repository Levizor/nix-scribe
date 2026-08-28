# nix-scribe - Agent Instructions

This document defines the core patterns and standards for `nix-scribe`. Adhere to these strictly to ensure consistency and quality.

## Implementation Standards
- **Minimal Comments**: Do not write comments for obvious code. Write concise docstrings only for complex functions where the name is not self-explanatory. **Do not use numbers in comments** (e.g. avoid `# 1.`, `# 2.` section headers).
- **Type Safety**: Use type hints for all function signatures and complex variables. Use modern lowercase types for collections (e.g., `list[str]`, `dict[str, Any]`, `tuple[int, ...]`) instead of importing from `typing` (e.g., `List`, `Dict`).
- **Scanner/Mapper Pattern**: Every module must follow the `BaseScanner` and `BaseMapper` architecture.
    - **Scanner**: Performs 100% pure filesystem-based scanning using `context.path_exists()`, `context.read_file()`, and `context.list_directory()`. **Never** invoke host binaries (`mount`, `systemctl`, `stat`) inside scanner functions. Returns an IR (Intermediate Representation).
    - **Mapper**: Transforms IR into `ConfigFragment` / `OptionBlock`.
- **System Context Privileges**: `SystemContext._run_command` is private and reserved strictly for internal privileged file fallback (`sudo cat`, `sudo ls`). Modules must never call shell execution functions.
- **Path Constants**: Define directory and configuration file path lists as constants at the top of the module file (e.g., `MODULES_PATHS = ["/etc/modules", "/etc/modules-load.d"]`) rather than hardcoding path strings inside scanner functions.
- **ConfigReader Abstraction**: Use `ConfigReader` and `read_merge_configs_from_paths_list` with dedicated parser functions instead of manually writing loops to scan and merge directory files.
- **Parser Location**: Place reusable parse functions in `src/nix_scribe/lib/parsers/<name>.py` with accompanying unit tests in `tests/lib/test_<name>_parser.py`, keeping module scanner files focused strictly on Scanner & Mapper logic.
- **Deep Merging**: Use the `deepmerge` library (specifically `always_merger`) when merging configurations in `ConfigReader`.
- **Directory Detection**: Use `os.path.isdir()` in `ConfigReader` to maintain compatibility with `unittest.mock` and ensure reliable directory detection in real systems.

## NixOS Options Discovery & Mapping
- **Authoritative Options Querying**: To discover or verify NixOS option names, types, and defaults, evaluate `nixpkgs` directly:
  `nix eval --json --impure --expr 'let eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; }; in builtins.attrNames eval.options.<attribute.path>'`
  For dynamic option sets (e.g. `services.<name>`, `luks.devices.<name>`):
  `nix eval --json --impure --expr 'let eval = import <nixpkgs/nixos/lib/eval-config.nix> { modules = []; }; in builtins.attrNames (eval.options.<path>.type.getSubOptions [])'`
- **Option Mapping Rules**:
  - Shared options (like `boot.loader.timeout`) belong in shared top-level fragments, not inside specific sub-modules.
  - Do not create NixOS-specific attributes for target system settings (e.g. `timeout` in `loader.conf` maps to `boot.loader.timeout`, NOT `boot.loader.systemd-boot.configurationLimit`).
  - Auto-detected settings (like Windows on the same ESP) should not generate redundant config.

## Testing Standards
- **Filesystem-backed Tests**: Use `pytest`'s `tmp_path` fixture for all module and parser tests.
    - Do **not** use complex, nested `unittest.mock` calls to simulate the filesystem.
    - Manually create the required directory structure and files within `tmp_path`.
    - Pass `tmp_path` to `SystemContext(root=tmp_path)`.
- **Mocking Strategy**: Only mock non-filesystem interactions such as:
    - `systemctl` status (`context.systemctl.is_enabled`).
    - Binary discovery (`context.find_executable_path`).
- **Integration Tests**: Use the existing `tests/systems/generic` root for full-system integration verification.

## Git & Workflow
- **Commit Messages**: Prefer concise, lowercase messages (e.g., `fix: ...`, `feat: ...`, `docs: ...`, `style: ...`, `refactor: ...`). Focus on the "what" and "why".
- **Isolated Feature Branches & PRs**: Create separate git branches and PRs for each distinct feature or refactoring. Do not mix unrelated documentation or refactoring into module feature branches.
- **Granular File Edits**: ALWAYS use targeted line edit tools (`replace_file_content`) to edit existing files and preserve diff views. NEVER use full-file overwrite tools (`write_to_file`) on existing files.
- **Tooling**: Always use `ruff check --fix` and `ruff format` before finalizing changes. Use `direnv exec . pytest` to ensure all tests pass in the correct environment.
- **Proactiveness**: If a bug is found in core libraries (like `ConfigReader`) during module development, fix it at the source rather than working around it in the module.

## Directory Structure
- `src/nix_scribe/modules/`: Module definitions organized by category.
- `src/nix_scribe/lib/`: Core logic, parsers, and writer.
- `src/nix_scribe/lib/parsers/`: Dedicated parser implementations.
- `tests/modules/`: Unit tests for individual modules using `tmp_path`.
- `tests/lib/`: Unit tests for parser implementations.
- `tests/systems/`: Static system roots for integration testing.
