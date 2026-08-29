from rich.console import Console

from nix_scribe.lib.registry import Module
from nix_scribe.nixscribe import NixScribe


def test_nixscribe_injection():
    console = Console(quiet=True)
    dummy_module = Module("test.dummy")
    modules = {"test.dummy": dummy_module}

    script = NixScribe(console=console, modules=modules)

    assert script.modules == modules
    assert "test.dummy" in script.results
    assert script.results["test.dummy"].module == dummy_module
