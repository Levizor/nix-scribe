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


def test_nixscribe_map_module_claims_packages():
    from nix_scribe.lib.option_block import ConfigFragment
    from nix_scribe.lib.packages import (
        DiscoveredPackage,
        InstallReason,
        PackageState,
        ResolvedPackage,
    )

    console = Console(quiet=True)
    git_pkg = ResolvedPackage(
        "git", DiscoveredPackage("git", "debian", InstallReason.EXPLICIT)
    )
    curl_pkg = ResolvedPackage(
        "curl", DiscoveredPackage("curl", "debian", InstallReason.EXPLICIT)
    )

    mod = Module("programs.git")

    @mod.scanner()
    def scan(context):
        return {"enable": True}

    @mod.mapper()
    def map_func(ir):
        return ConfigFragment(
            name="git",
            data={"programs.git.enable": True},
            claims={"git"},
        )

    script = NixScribe(console=console, modules={"programs.git": mod})
    script.context.packages = PackageState(packages=[git_pkg, curl_pkg])

    assert script.context.packages.unclaimed == [git_pkg, curl_pkg]

    result = script.results["programs.git"]
    result.scan_data = mod.scan(script.context)
    script._map_module(result)

    assert result.map_data is not None
    assert result.map_data.claims == {"git"}
    assert script.context.packages.is_claimed("git")
    assert script.context.packages.unclaimed == [curl_pkg]


def test_nixscribe_system_packages_claims_integration():
    from nix_scribe.lib.option_block import ConfigFragment
    from nix_scribe.lib.packages import (
        DiscoveredPackage,
        InstallReason,
        PackageState,
        ResolvedPackage,
    )
    from nix_scribe.modules.environment.system_packages import system_packages

    console = Console(quiet=True)
    git_pkg = ResolvedPackage(
        "git", DiscoveredPackage("git", "debian", InstallReason.EXPLICIT)
    )
    curl_pkg = ResolvedPackage(
        "curl", DiscoveredPackage("curl", "debian", InstallReason.EXPLICIT)
    )

    git_mod = Module("programs.git")

    @git_mod.scanner()
    def scan_git(context):
        return {"enable": True}

    @git_mod.mapper()
    def map_git(ir):
        return ConfigFragment(
            name="git",
            data={"programs.git.enable": True},
            claims={"git"},
        )

    script = NixScribe(
        console=console,
        modules={
            "programs.git": git_mod,
            "environment.system_packages": system_packages,
        },
    )
    script.context.packages = PackageState(packages=[git_pkg, curl_pkg])

    # Scan phase
    for res in script.results.values():
        script._scan_module(res)

    # Map phase
    for res in script.results.values():
        script._map_module(res)

    sys_res = script.results["environment.system_packages"]
    assert sys_res.map_data is not None
    rendered_options = sys_res.map_data.options
    assert "environment.systemPackages" in rendered_options
    # Only curl should be in environment.systemPackages because git was claimed during map
    assert script.context.packages.is_claimed("git")
    assert not script.context.packages.is_claimed("curl")

    from nix_scribe.lib.nix_writer import NixWriter
    from nix_scribe.lib.nixfile import NixFile

    nix_file = NixFile("configuration")
    nix_file.add_fragment(sys_res.map_data)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "curl" in output
    assert "git" not in output
