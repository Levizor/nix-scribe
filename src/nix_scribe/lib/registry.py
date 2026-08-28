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
        ModuleRegistry.get_instance().register(self)

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

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}
        self.default_blacklist: set[str] = set()

    @classmethod
    def get_instance(cls) -> "ModuleRegistry":
        """Returns the global singleton instance of ModuleRegistry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets the singleton instance (useful for clean unit testing)."""
        cls._instance = cls()

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
