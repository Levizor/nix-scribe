import fnmatch
from typing import Any, Callable, ClassVar

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


class ModuleRegistry:
    """
    Singleton registry managing registered modules, default blacklist/whitelist states, and CLI filtering.
    """

    _instance: ClassVar["ModuleRegistry | None"] = None

    def __new__(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self) -> None:
        """Resets the singleton registry instance state (useful for clean unit testing)."""
        self._modules: dict[str, Module] = {}
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
        result = []
        for entry in patterns:
            for item in entry.split(","):
                cleaned = item.strip()
                if cleaned:
                    result.append(cleaned)
        return result

    def is_match(self, name: str, patterns: list[str]) -> bool:
        """Returns True if module name matches any pattern (exact or fnmatch wildcard)."""
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(name, f"{pattern}.*"):
                return True
        return False

    def filter(
        self,
        enable: list[str] | None = None,
        disable: list[str] | None = None,
        only: list[str] | None = None,
    ) -> dict[str, Module]:
        """
        Filters modules based on default_blacklist, --only, --enable-module (-e), and --disable-module (-d).
        """
        enable_patterns = self._parse_patterns(enable)
        disable_patterns = self._parse_patterns(disable)
        only_patterns = self._parse_patterns(only)

        filtered: dict[str, Module] = {}

        for name, mod in self._modules.items():
            is_default_blacklisted = self.is_match(name, list(self.default_blacklist))

            if only_patterns and not self.is_match(name, only_patterns):
                continue

            is_cli_enabled = (
                self.is_match(name, enable_patterns) if enable_patterns else False
            )

            is_cli_disabled = (
                self.is_match(name, disable_patterns) if disable_patterns else False
            )

            if is_cli_disabled and not is_cli_enabled:
                continue

            if is_default_blacklisted and not is_cli_enabled:
                continue

            filtered[name] = mod

        return filtered


def print_modules_table(console: Any = None) -> None:
    """
    Prints a formatted table of all discovered modules and their default status using Rich (with fallback).
    """
    from rich.console import Console
    from rich.table import Table

    from nix_scribe.lib.loader import ModuleLoader

    loader = ModuleLoader()
    modules = loader.discover()
    registry = ModuleRegistry()

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
            is_disabled = registry.is_match(name, list(registry.default_blacklist))
            status = (
                "[yellow]disabled (default)[/yellow]"
                if is_disabled
                else "[green]enabled[/green]"
            )
            table.add_row(name, category, status)

        console.print(table)
    except Exception:
        print("nix-scribe Discovered Modules:")
        print(f"{'Module Name':<35} {'Category':<15} {'Status'}")
        print("-" * 65)
        for name in sorted(modules.keys()):
            category = name.split(".")[0]
            is_disabled = registry.is_match(name, list(registry.default_blacklist))
            status = "disabled (default)" if is_disabled else "enabled"
            print(f"{name:<35} {category:<15} {status}")


def print_modules_tree(console: Any = None) -> None:
    """
    Prints a hierarchical tree view of all discovered modules and their default status using Rich (with fallback).
    """
    from rich.console import Console
    from rich.tree import Tree

    from nix_scribe.lib.loader import ModuleLoader

    loader = ModuleLoader()
    modules = loader.discover()
    registry = ModuleRegistry()

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

            is_disabled = registry.is_match(name, list(registry.default_blacklist))
            status = (
                "[yellow](disabled by default)[/yellow]"
                if is_disabled
                else "[green](enabled)[/green]"
            )
            current_tree.add(f"[cyan]{parts[-1]}[/cyan] {status}")

        console.print(root_tree)
    except Exception:
        print("nix-scribe Modules Tree:")
        for name in sorted(modules.keys()):
            is_disabled = registry.is_match(name, list(registry.default_blacklist))
            status = "(disabled by default)" if is_disabled else "(enabled)"
            print(f"  - {name} {status}")
