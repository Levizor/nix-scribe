import importlib
import logging
import pkgutil
from pathlib import Path

from nix_scribe.modules.base import Module

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

    def discover(self) -> dict[str, list[Module]]:
        """
        Discovers modules and organizes them by first-level name
        """
        categories: dict[str, list[Module]] = {}

        for item in self.package_path.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                category_name = item.name
                categories[category_name] = self._load_modules_in_category(
                    category_name
                )

        return categories

    def _load_modules_in_category(self, category: str) -> list[Module]:
        modules = []
        category_package = f"{self.modules_package}.{category}"

        spec = importlib.util.find_spec(category_package)
        if not spec or not spec.submodule_search_locations:
            return []

        category_path = spec.submodule_search_locations

        for info in pkgutil.walk_packages(category_path, f"{category_package}."):
            if info.ispkg:
                continue

            try:
                mod = importlib.import_module(info.name)
                if hasattr(mod, "module") and isinstance(mod.module, Module):
                    logger.debug(f"Loaded module '{mod.module.name}' from {info.name}")
                    modules.append(mod.module)
                else:
                    logger.debug(
                        f"Skipped {info.name}: no 'module' object of type Module found"
                    )
            except Exception as e:
                logger.error(f"Failed to load module {info.name}: {e}")

        return modules
