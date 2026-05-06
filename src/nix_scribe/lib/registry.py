from typing import Any, Callable

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import BaseOptionBlock

_MODULES_REGISTRY: dict[str, "Module"] = {}

ScannerFunc = Callable[[SystemContext], dict[str, Any]]
MapperFunc = Callable[[dict[str, Any]], BaseOptionBlock | None]


class Module:
    def __init__(self, name: str) -> None:
        self.name = name
        self.scan: ScannerFunc | None = None
        self.map: MapperFunc | None = None
        _MODULES_REGISTRY[self.name] = self

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
