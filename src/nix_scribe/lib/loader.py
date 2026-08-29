import importlib
import importlib.util
import logging
import pkgutil
import sys
from pathlib import Path

from nix_scribe.lib.registry import Module, ModuleRegistry

logger = logging.getLogger(__name__)


class ModuleLoader:
    def __init__(
        self,
        modules_package: str | None = "nix_scribe.modules",
        path: Path | None = None,
    ):
        self.modules_package = modules_package
        if path:
            self.package_path = Path(path)
            if not self.package_path.exists():
                raise FileNotFoundError(
                    f"Plugin path does not exist: '{self.package_path}'"
                )
            search_dir = (
                self.package_path.parent
                if self.package_path.is_file()
                else self.package_path
            )
            if str(search_dir) not in sys.path:
                sys.path.insert(0, str(search_dir))
        elif modules_package:
            spec = importlib.util.find_spec(modules_package)
            if not spec or not spec.submodule_search_locations:
                raise ImportError(f"Could not find package {modules_package}")
            self.package_path = Path(spec.submodule_search_locations[0])
        else:
            self.package_path = None

    def discover(self) -> dict[str, Module]:
        """Loads all modules and returns a flat dictionary keyed by namespace."""
        self._import_all_modules()

        valid_modules: dict[str, Module] = {}

        for full_name, module in ModuleRegistry().get_all().items():
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
        if not self.package_path:
            return

        if self.package_path.is_file():
            if self.package_path.suffix == ".py":
                module_name = self.package_path.stem
                try:
                    spec = importlib.util.spec_from_file_location(
                        module_name, self.package_path
                    )
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = mod
                        spec.loader.exec_module(mod)
                except Exception as e:
                    logger.error(f"Failed to load module file {self.package_path}: {e}")
            return

        package_paths = [str(self.package_path)]
        prefix = f"{self.modules_package}." if self.modules_package else ""

        for info in pkgutil.walk_packages(package_paths, prefix):
            if info.ispkg:
                continue
            try:
                if info.name in sys.modules:
                    importlib.reload(sys.modules[info.name])
                else:
                    importlib.import_module(info.name)
            except Exception as e:
                logger.error(f"Failed to load module {info.name}: {e}")
