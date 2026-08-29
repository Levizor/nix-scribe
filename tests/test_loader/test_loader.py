from pathlib import Path

from nix_scribe.lib.loader import ModuleLoader


def test_module_loader_discovery_logic():
    from nix_scribe.lib.registry import ModuleRegistry

    registry = ModuleRegistry()
    saved = dict(registry._modules)
    registry.clear()

    try:
        pkg_dir = Path(__file__).parent / "test_loader_pkg"
        loader = ModuleLoader(
            modules_package="tests.test_loader.test_loader_pkg", path=pkg_dir
        )
        modules = loader.discover()

        assert "dummy" in modules
        mod = modules["dummy"]
        assert mod.name == "dummy"
    finally:
        registry._modules = saved


def test_module_loader_real_discovery():
    loader = ModuleLoader()
    modules = loader.discover()

    assert len(modules) > 0
    # Check for a few well-known modules
    assert "programs.bash" in modules
    assert "programs.git" in modules

    assert modules["programs.bash"].name == "programs.bash"
