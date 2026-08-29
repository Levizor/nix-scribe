import fnmatch
import re
from dataclasses import dataclass
from typing import Any, Callable, ClassVar, Sequence

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment

ScannerFunc = Callable[[SystemContext], dict[str, Any]]
MapperFunc = Callable[[dict[str, Any]], ConfigFragment | None]


@dataclass(frozen=True)
class ModuleFilter:
    """Immutable value object holding parsed module filter rules."""

    enable: tuple[str, ...] = ()
    disable: tuple[str, ...] = ()
    only: tuple[str, ...] = ()

    @classmethod
    def from_raw(
        cls,
        enable: list[str] | None = None,
        disable: list[str] | None = None,
        only: list[str] | None = None,
    ) -> "ModuleFilter":
        """Parses raw CLI pattern inputs ONCE into clean immutable tuples."""
        return cls(
            enable=tuple(cls._parse(enable)),
            disable=tuple(cls._parse(disable)),
            only=tuple(cls._parse(only)),
        )

    @staticmethod
    def _parse(patterns: list[str] | None) -> list[str]:
        if not patterns:
            return []
        return [
            item.strip()
            for entry in patterns
            for item in entry.split(",")
            if item.strip()
        ]

    def matches(self, name: str, patterns: Sequence[str]) -> bool:
        """Returns True if module name matches any pattern in patterns."""
        return any(
            fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(name, f"{pat}.*")
            for pat in patterns
        )

    def is_active(self, name: str, is_default_blacklisted: bool) -> bool:
        """Determines if a module is active under this filter spec."""
        if self.only and not self.matches(name, self.only):
            return False

        is_cli_enabled = bool(self.enable and self.matches(name, self.enable))
        is_cli_disabled = bool(self.disable and self.matches(name, self.disable))

        if (is_cli_disabled or is_default_blacklisted) and not is_cli_enabled:
            return False

        return True

    def get_status(self, name: str, is_default_blacklisted: bool) -> str:
        """Computes the status label for a module under this filter spec."""
        if self.is_active(name, is_default_blacklisted):
            if is_default_blacklisted and self.matches(name, self.enable):
                return "[green]enabled (via CLI)[/green]"
            return "[green]enabled[/green]"
        else:
            if self.disable and self.matches(name, self.disable):
                return "[yellow]disabled (via CLI)[/yellow]"
            if self.only and not self.matches(name, self.only):
                return "[dim]excluded (--only)[/dim]"
            if is_default_blacklisted:
                return "[yellow]disabled (default)[/yellow]"
            return "[yellow]disabled[/yellow]"


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
        return ModuleFilter._parse(patterns)

    @staticmethod
    def is_match(name: str, patterns: list[str]) -> bool:
        """Returns True if module name matches any pattern (exact or fnmatch wildcard)."""
        return ModuleFilter().matches(name, patterns)

    def validate_patterns(
        self,
        modules: dict[str, Module] | None = None,
        enable: list[str] | None = None,
        disable: list[str] | None = None,
        only: list[str] | None = None,
        filter_spec: ModuleFilter | None = None,
    ) -> None:
        """
        Validates that all user-supplied patterns match at least one available module.
        """
        spec = filter_spec or ModuleFilter.from_raw(
            enable=enable, disable=disable, only=only
        )
        target_modules = self._modules if modules is None else modules
        options = [
            (spec.enable, "--enable-module (-e)"),
            (spec.disable, "--disable-module (-d)"),
            (spec.only, "--only"),
        ]

        for patterns, option_name in options:
            for pattern in patterns:
                if not any(spec.matches(name, [pattern]) for name in target_modules):
                    raise InvalidModuleError(
                        f"Module pattern '{pattern}' specified in {option_name} did not match any available module."
                    )

    def filter(
        self,
        modules: dict[str, Module] | None = None,
        enable: list[str] | None = None,
        disable: list[str] | None = None,
        only: list[str] | None = None,
        filter_spec: ModuleFilter | None = None,
    ) -> dict[str, Module]:
        """
        Filters modules based on default_blacklist, --only, --enable-module (-e), and --disable-module (-d).
        """
        spec = filter_spec or ModuleFilter.from_raw(
            enable=enable, disable=disable, only=only
        )
        target_modules = self._modules if modules is None else modules
        self.validate_patterns(target_modules, filter_spec=spec)

        blacklist = list(self.default_blacklist)
        return {
            name: mod
            for name, mod in target_modules.items()
            if spec.is_active(name, self.is_match(name, blacklist))
        }


def _strip_markup(text: str) -> str:
    """Strips Rich console color/style tags from a string for plain text fallback."""
    return re.sub(r"\[.*?\]", "", text)


def _prepare_module_statuses(
    modules: dict[str, Module] | None = None,
    filter_spec: ModuleFilter | None = None,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    only: list[str] | None = None,
) -> tuple[dict[str, Module], dict[str, str]]:
    """
    Computes rich status strings for each valid module.
    """
    if modules is None:
        from nix_scribe.lib.loader import ModuleLoader

        loader = ModuleLoader()
        target_modules = loader.discover()
    else:
        target_modules = modules

    registry = ModuleRegistry()

    spec = filter_spec or ModuleFilter.from_raw(
        enable=enable, disable=disable, only=only
    )
    blacklist = list(registry.default_blacklist)

    registry.validate_patterns(target_modules, filter_spec=spec)

    statuses = {
        name: spec.get_status(name, registry.is_match(name, blacklist))
        for name in target_modules
    }

    return target_modules, statuses


def print_modules_table(
    console: Console | None = None,
    modules: dict[str, Module] | None = None,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    only: list[str] | None = None,
    filter_spec: ModuleFilter | None = None,
) -> None:
    """
    Prints a formatted table of all discovered modules and their status using Rich (with fallback).
    """
    target_modules, statuses = _prepare_module_statuses(
        modules=modules,
        filter_spec=filter_spec,
        enable=enable,
        disable=disable,
        only=only,
    )

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

        for name in sorted(target_modules.keys()):
            category = name.split(".")[0]
            table.add_row(name, category, statuses[name])

        console.print(table)
    except Exception:
        print("nix-scribe Discovered Modules:")
        print(f"{'Module Name':<35} {'Category':<15} {'Status'}")
        print("-" * 65)
        for name in sorted(target_modules.keys()):
            category = name.split(".")[0]
            print(f"{name:<35} {category:<15} {_strip_markup(statuses[name])}")


def print_modules_tree(
    console: Console | None = None,
    modules: dict[str, Module] | None = None,
    enable: list[str] | None = None,
    disable: list[str] | None = None,
    only: list[str] | None = None,
    filter_spec: ModuleFilter | None = None,
) -> None:
    """
    Prints a hierarchical tree view of all discovered modules and their status using Rich (with fallback).
    """
    target_modules, statuses = _prepare_module_statuses(
        modules=modules,
        filter_spec=filter_spec,
        enable=enable,
        disable=disable,
        only=only,
    )

    if console is None:
        console = Console()

    try:
        root_tree = Tree("nix-scribe Modules", guide_style="bold bright_blue")
        nodes: dict[str, Tree] = {}

        for name in sorted(target_modules.keys()):
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
        for name in sorted(target_modules.keys()):
            print(f"  - {name} ({_strip_markup(statuses[name])})")
