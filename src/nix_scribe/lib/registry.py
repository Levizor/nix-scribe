import fnmatch
import re
from typing import Any, Callable, ClassVar

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment

ScannerFunc = Callable[[SystemContext], dict[str, Any]]
MapperFunc = Callable[[dict[str, Any]], ConfigFragment | None]


class Module:
    def __init__(self, name: str) -> None:
        self.name = name
        self.scan: ScannerFunc | None = None
        self.map: MapperFunc | None = None
        ModuleRegistry().register(self)

    def scanner(self) -> Callable[[ScannerFunc], ScannerFunc]:
        """Decorator to register the scanner function."""

        def decorator(func: ScannerFunc) -> ScannerFunc:
            self.scan = func
            return func

        return decorator

    def mapper(self) -> Callable[[MapperFunc], MapperFunc]:
        """Decorator to register the mapper function."""

        def decorator(func: MapperFunc) -> MapperFunc:
            self.map = func
            return func

        return decorator


class InvalidModuleError(ValueError):
    """Raised when a user-specified module pattern does not match any registered module."""

    pass


class ModuleRegistry:
    """
    Singleton registry managing registered modules, default blacklist/whitelist states, and CLI filtering.
    """

    _instance: ClassVar["ModuleRegistry | None"] = None

    def __new__(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules: dict[str, Module] = {}
            cls._instance.reset()
        return cls._instance

    def reset(self) -> None:
        """Resets default blacklist and filter state without wiping loaded modules."""
        self.default_blacklist: set[str] = {"boot.kernel"}

    def register(self, module: Module) -> None:
        """Registers a module in the registry."""
        self._modules[module.name] = module

    def get_all(self) -> dict[str, Module]:
        """Returns a copy of all registered modules."""
        return dict(self._modules)

    def clear(self) -> None:
        """Clears registered modules."""
        self._modules.clear()

    @staticmethod
    def _parse_patterns(patterns: list[str] | None) -> list[str]:
        """Splits comma-separated or list pattern entries into a clean list of strings."""
        if not patterns:
            return []
        return [
            item.strip()
            for entry in patterns
            for item in entry.split(",")
            if item.strip()
        ]

    @staticmethod
    def is_match(name: str, patterns: list[str]) -> bool:
        """Returns True if module name matches any pattern (exact or fnmatch wildcard)."""
        return any(
            fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(name, f"{pat}.*")
            for pat in patterns
        )

    def validate_patterns(
        self,
        modules: dict[str, Module] | None = None,
        enable: list[str] | None = None,
        disable: list[str] | None = None,
        only: list[str] | None = None,
    ) -> None:
        """
        Validates that all user-supplied patterns match at least one available module.
        """
        target_modules = self._modules if modules is None else modules
        options = [
            (enable, "--enable-module (-e)"),
            (disable, "--disable-module (-d)"),
            (only, "--only"),
        ]

        for raw_patterns, option_name in options:
            parsed = self._parse_patterns(raw_patterns)
            for pattern in parsed:
                if not any(self.is_match(name, [pattern]) for name in target_modules):
                    raise InvalidModuleError(
                        f"Module pattern '{pattern}' specified in {option_name} did not match any available module."
                    )

    def filter(
        self,
        modules: dict[str, Module] | None = None,
        enable: list[str] | None = None,
        disable: list[str] | None = None,
        only: list[str] | None = None,
    ) -> dict[str, Module]:
        """
        Filters modules based on default_blacklist, --only, --enable-module (-e), and --disable-module (-d).
        """
        target_modules = self._modules if modules is None else modules
        self.validate_patterns(
            target_modules, enable=enable, disable=disable, only=only
        )

        enable_patterns = self._parse_patterns(enable)
        disable_patterns = self._parse_patterns(disable)
        only_patterns = self._parse_patterns(only)

        filtered: dict[str, Module] = {}

        for name, mod in target_modules.items():
            is_default_blacklisted = self.is_match(name, list(self.default_blacklist))

            if only_patterns and not self.is_match(name, only_patterns):
                continue

            is_cli_enabled = bool(
                enable_patterns and self.is_match(name, enable_patterns)
            )
            is_cli_disabled = bool(
                disable_patterns and self.is_match(name, disable_patterns)
            )

            if (is_cli_disabled or is_default_blacklisted) and not is_cli_enabled:
                continue

            filtered[name] = mod

        return filtered


def _strip_markup(text: str) -> str:
    """Strips Rich console color/style tags from a string for plain text fallback."""
    return re.sub(r"\[.*?\]", "", text)


def _prepare_module_statuses(
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    only: list[str] | None = None,
) -> tuple[dict[str, Module], dict[str, str]]:
    """
    Discovers valid modules and computes rich status strings for each module.
    """
    from nix_scribe.lib.loader import ModuleLoader

    loader = ModuleLoader()
    modules = loader.discover()
    registry = ModuleRegistry()

    enable_patterns = registry._parse_patterns(enable)
    disable_patterns = registry._parse_patterns(disable)
    only_patterns = registry._parse_patterns(only)

    active_modules = registry.filter(
        modules=modules, enable=enable, disable=disable, only=only
    )

    statuses: dict[str, str] = {}
    for name in modules:
        is_active = name in active_modules
        is_default_blacklisted = registry.is_match(
            name, list(registry.default_blacklist)
        )

        if is_active:
            if is_default_blacklisted and registry.is_match(name, enable_patterns):
                statuses[name] = "[green]enabled (via CLI)[/green]"
            else:
                statuses[name] = "[green]enabled[/green]"
        else:
            if disable_patterns and registry.is_match(name, disable_patterns):
                statuses[name] = "[yellow]disabled (via CLI)[/yellow]"
            elif only_patterns and not registry.is_match(name, only_patterns):
                statuses[name] = "[dim]excluded (--only)[/dim]"
            elif is_default_blacklisted:
                statuses[name] = "[yellow]disabled (default)[/yellow]"
            else:
                statuses[name] = "[yellow]disabled[/yellow]"

    return modules, statuses


def print_modules_table(
    console: Console | None = None,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    only: list[str] | None = None,
) -> None:
    """
    Prints a formatted table of all discovered modules and their status using Rich (with fallback).
    """
    modules, statuses = _prepare_module_statuses(enable, disable, only)

    if console is None:
        console = Console()

    try:
        table = Table(
            title="nix-scribe Discovered Modules",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Module Name", style="cyan")
        table.add_column("Category", style="blue")
        table.add_column("Status", style="bold")

        for name in sorted(modules.keys()):
            category = name.split(".")[0]
            table.add_row(name, category, statuses[name])

        console.print(table)
    except Exception:
        print("nix-scribe Discovered Modules:")
        print(f"{'Module Name':<35} {'Category':<15} {'Status'}")
        print("-" * 65)
        for name in sorted(modules.keys()):
            category = name.split(".")[0]
            print(f"{name:<35} {category:<15} {_strip_markup(statuses[name])}")


def print_modules_tree(
    console: Console | None = None,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    only: list[str] | None = None,
) -> None:
    """
    Prints a hierarchical tree view of all discovered modules and their status using Rich (with fallback).
    """
    modules, statuses = _prepare_module_statuses(enable, disable, only)

    if console is None:
        console = Console()

    try:
        root_tree = Tree("nix-scribe Modules", guide_style="bold bright_blue")
        nodes: dict[str, Tree] = {}

        for name in sorted(modules.keys()):
            parts = name.split(".")
            current_tree = root_tree

            for i in range(len(parts) - 1):
                path = ".".join(parts[: i + 1])
                if path not in nodes:
                    nodes[path] = current_tree.add(f"[bold blue]{parts[i]}[/bold blue]")
                current_tree = nodes[path]

            current_tree.add(f"[cyan]{parts[-1]}[/cyan] ({statuses[name]})")

        console.print(root_tree)
    except Exception:
        print("nix-scribe Modules Tree:")
        for name in sorted(modules.keys()):
            print(f"  - {name} ({_strip_markup(statuses[name])})")
