# nix-scribe - Agent Instructions

This document defines the core patterns and standards for `nix-scribe`. Adhere to these strictly to ensure consistency and quality.

## Implementation Standards
- **Tone & Language**: Write dead simple, clear developer English. Never use marketing fluff, AI buzzwords, or overly verbose explanations.
- **Minimal Comments**: Do not write comments for obvious code. Write concise docstrings only for complex functions where the name is not self-explanatory. **Do not use numbers in comments** (e.g. avoid `# 1.`, `# 2.` section headers).
- **Type Safety**: Use type hints for all function signatures and complex variables. Use modern lowercase types for collections (e.g., `list[str]`, `dict[str, Any]`, `tuple[int, ...]`) instead of importing from `typing` (e.g., `List`, `Dict`).
- **Module & Scanner Pattern**:
    - **Declarative Contract (`NixModule`)**: Defined in `src/nix_scribe/modules/nixos/<category>/<name>.py` by subclassing `NixModule(prefix="<option.prefix>", claims={"<pkg>"})` and declaring options via `option(...)`.
    - **Scanner (`Scanner`)**: Defined in `src/nix_scribe/scanners/<category>/<name>.py` by instantiating `Scanner("<category>.<name>", phase=ScannerPhase.NORMAL)` and decorating `scan(context: SystemContext) -> <Contract> | None` with `@<scanner>.scanner()`. Performs pure filesystem-based scanning via `SystemContext` (`path_exists`, `read_file`, `read_file_bytes`, `list_directory`, `find_executable_path`). **Never** invoke host binaries (`mount`, `systemctl`, `stat`).
- **Package Claiming**: Modules managing tools or services declare claimed packages statically on their `NixModule` class (`claims={"<pkg>"}`), conditionally on individual options (`option(..., claims={"<pkg>"})`), or dynamically via `mod.claim("<pkg>")`. `NixScribe` registers active claims in `context.packages` during the scan pass so claimed packages are not duplicated in `environment.systemPackages`.
- **Execution Phases**: Use `ScannerPhase.EARLY` (10), `ScannerPhase.NORMAL` (50, default), or `ScannerPhase.LATE` (100). Aggregators like `environment.system_packages` run in `LATE` to process unclaimed packages.
- **Package Managers**: Distro package managers subclass `PackageManager` in `src/nix_scribe/lib/packages/managers/` and register with `register_package_manager`.
- **System Context Privileges**: `SystemContext._run_command` is private and reserved strictly for internal privileged file fallback (`sudo cat`, `sudo test`). Modules must never execute shell commands.
- **Path Constants**: Define directory and configuration file path lists as constants at the top of the module file (e.g., `MODULES_PATHS = ["/etc/modules", "/etc/modules-load.d"]`) rather than hardcoding path strings inside scanner functions.
- **ConfigReader Abstraction**: Use `ConfigReader` and its `read_merge_configs_from_paths_list` method with dedicated parser functions instead of manually writing loops to scan and merge directory files.
- **Parser Location**: Place reusable parse functions in `src/nix_scribe/lib/parsers/<name>.py` with accompanying unit tests in `tests/lib/test_<name>_parser.py`, keeping scanner files focused strictly on host inspection and `NixModule` population.
- **Deep Merging**: `ConfigReader` handles dictionary merging internally via `always_merger`. Modules must never import `deepmerge` or perform manual merges.
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
- `src/nix_scribe/modules/nixos/`: Declarative `NixModule` contracts organized by NixOS category.
- `src/nix_scribe/scanners/`: Single-stage `Scanner` implementations organized by category.
- `src/nix_scribe/lib/`: Core logic (`nix_module.py`, `emitter.py`, `nix_fragment.py`, `registry.py`, `scheduler.py`, `nix_writer.py`).
- `src/nix_scribe/lib/parsers/`: Dedicated parser implementations.
- `src/nix_scribe/lib/packages/`: Package managers (`managers/`), models, and resolvers.
- `src/nix_scribe/cli/`: CLI entrypoint (`main.py`), arguments (`arguments.py`), and logging (`logger.py`).
- `tests/scanners/`: Unit tests for individual scanners using `tmp_path`.
- `tests/lib/`: Unit tests for core library and parser implementations.
- `tests/lib/packages/`: Unit tests for package managers and resolvers.
- `tests/systems/`: Static system roots for integration testing.
