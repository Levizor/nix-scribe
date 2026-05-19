import importlib
import importlib.util
import logging
import pkgutil
from pathlib import Path

from nix_scribe.lib.registry import _MODULES_REGISTRY, Module

logger = logging.getLogger(__name__)


class ModuleLoader:
    def __init__(
        self, modules_package: str = "nix_scribe.modules", path: Path | None = None
    ):
        self.modules_package = modules_package
        if path:
            self.package_path = path
        else:
            spec = importlib.util.find_spec(modules_package)
            if not spec or not spec.submodule_search_locations:
                raise ImportError(f"Could not find package {modules_package}")
            self.package_path = Path(spec.submodule_search_locations[0])

    def discover(self) -> dict[str, Module]:
        """Loads all modules and returns a flat dictionary keyed by namespace."""
        self._import_all_modules()

        valid_modules: dict[str, Module] = {}

        for full_name, module in _MODULES_REGISTRY.items():
            if not module.scan:
                logger.warning(f"Module '{full_name}' skipped: No scanner.")
                continue
            if not module.map:
                logger.warning(f"Module '{full_name}' skipped: No mapper.")
                continue

            valid_modules[full_name] = module
            logger.debug(f"Successfully loaded module '{full_name}'")

        return valid_modules

    def _import_all_modules(self) -> None:
        spec = importlib.util.find_spec(self.modules_package)
        if not spec or not spec.submodule_search_locations:
            return

        package_path = spec.submodule_search_locations

        for info in pkgutil.walk_packages(package_path, f"{self.modules_package}."):
            if info.ispkg:
                continue

            try:
                importlib.import_module(info.name)
            except Exception as e:
                logger.error(f"Failed to load module {info.name}: {e}")
