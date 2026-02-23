from pathlib import Path
from nix_scribe.lib.loader import ModuleLoader

def test_module_loader_discovery_logic():
    # Point to the directory next to this file
    pkg_dir = Path(__file__).parent / "test_loader_pkg"
    
    # Use the full import path relative to the project root
    loader = ModuleLoader(modules_package="tests.test_loader.test_loader_pkg", path=pkg_dir)
    categories = loader.discover()
    
    assert "test_category" in categories
    mods = categories["test_category"]
    assert len(mods) == 1
    assert mods[0].name == "dummy"

def test_module_loader_real_discovery():
    loader = ModuleLoader()
    categories = loader.discover()
    
    assert len(categories) > 0
    assert "programs" in categories
    
    all_names = [m.name for mods in categories.values() for m in mods]
    assert "bash" in all_names
