from pathlib import Path

from nix_scribe.lib.loader import ModuleLoader


def test_module_loader_discovery_logic():
    # Point to the directory next to this file
    pkg_dir = Path(__file__).parent / "test_loader_pkg"

    # Use the full import path relative to the project root
    loader = ModuleLoader(
        modules_package="tests.test_loader.test_loader_pkg", path=pkg_dir
    )
    modules = loader.discover()

    assert "dummy" in modules
    mod = modules["dummy"]
    assert mod.name == "dummy"


def test_module_loader_real_discovery():
    loader = ModuleLoader()
    modules = loader.discover()

    assert len(modules) > 0
    # Check for a few well-known modules
    assert "programs.bash" in modules
    assert "programs.git" in modules

    assert modules["programs.bash"].name == "programs.bash"
