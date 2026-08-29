import pytest

from nix_scribe.lib.loader import ModuleLoader
from nix_scribe.lib.registry import ModuleRegistry


def test_plugin_loader_single_file(tmp_path):
    registry = ModuleRegistry()
    saved = dict(registry._modules)
    registry.clear()

    try:
        plugin_file = tmp_path / "my_custom_plugin.py"
        plugin_file.write_text(
            "from nix_scribe.lib.registry import Module\n"
            "mod = Module('services.custom_service')\n"
            "@mod.scanner()\n"
            "def scan(ctx): return {'enable': True}\n"
            "@mod.mapper()\n"
            "def map(ir): return None\n"
        )

        loader = ModuleLoader(modules_package=None, path=plugin_file)
        modules = loader.discover()

        assert "services.custom_service" in modules
        assert modules["services.custom_service"].name == "services.custom_service"
    finally:
        registry._modules = saved


def test_plugin_loader_directory_without_init(tmp_path):
    registry = ModuleRegistry()
    saved = dict(registry._modules)
    registry.clear()

    try:
        plugin_dir = tmp_path / "plugins_dir"
        plugin_dir.mkdir()
        (plugin_dir / "plugin_one.py").write_text(
            "from nix_scribe.lib.registry import Module\n"
            "mod = Module('services.plugin_one')\n"
            "@mod.scanner()\n"
            "def scan(ctx): return {'enable': True}\n"
            "@mod.mapper()\n"
            "def map(ir): return None\n"
        )

        loader = ModuleLoader(modules_package=None, path=plugin_dir)
        modules = loader.discover()

        assert "services.plugin_one" in modules
    finally:
        registry._modules = saved


def test_plugin_loader_nonexistent_path(tmp_path):
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        ModuleLoader(modules_package=None, path=non_existent)
