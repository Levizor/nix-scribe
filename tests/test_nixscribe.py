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
    assert script.context.packages.claimed_by("git") == "programs.git"
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

    asset = next(iter(sys_res.map_data.assets))
    assert "Claimed packages:" in asset.content
    assert "git # from debian:git (claimed by programs.git)" in asset.content


def test_nixscribe_run_progress_and_debug_logging(tmp_path, caplog):
    import logging

    from nix_scribe.arguments import args
    from nix_scribe.lib.option_block import ConfigFragment

    args.output_path = tmp_path / "nix-config"

    dummy_mod = Module("test.dummy")

    @dummy_mod.scanner()
    def scan(context):
        return {"enabled": True}

    @dummy_mod.mapper()
    def map_func(ir):
        return ConfigFragment(name="dummy", data={"programs.dummy.enable": True})

    console = Console(quiet=True)
    script = NixScribe(console=console, modules={"test.dummy": dummy_mod})

    with caplog.at_level(logging.DEBUG):
        script.run()

    # Per-module messages are now logged at DEBUG level
    assert "Scanned test.dummy" in caplog.text
    assert "Mapped test.dummy" in caplog.text

    # Milestone messages are logged at INFO level
    assert "Starting nix-scribe system scan..." in caplog.text
    assert "Finished system scan in" in caplog.text
    assert "Finished mapping stage in" in caplog.text
    assert "Writing configuration..." in caplog.text
    assert (tmp_path / "nix-config" / "configuration.nix").exists()


def test_nixscribe_scan_module_elevation_pause():
    from unittest.mock import MagicMock

    from nix_scribe.lib.context import ElevationRequest

    dummy_mod = Module("test.restricted")

    @dummy_mod.scanner()
    def scan(context):
        raise ElevationRequest("/etc/shadow", "Requires root")

    console = Console(quiet=True)
    script = NixScribe(console=console, modules={"test.restricted": dummy_mod})

    mock_progress = MagicMock()
    script._prompt_for_sudo = MagicMock(return_value=False)

    res = script.results["test.restricted"]
    script._scan_module(res, progress=mock_progress)

    # Progress bar was stopped for prompt and resumed
    mock_progress.stop.assert_called_once()
    mock_progress.start.assert_called_once()
    assert res.scan_data == {}


def test_nixscribe_run_dump_ir(tmp_path):
    import json

    from nix_scribe.arguments import args
    from nix_scribe.lib.option_block import ConfigFragment

    args.output_path = tmp_path / "nix-config"
    args.dump_ir = True

    dummy_mod = Module("test.dummy")

    @dummy_mod.scanner()
    def scan(context):
        return {"option": "value", "password": "supersecret"}

    @dummy_mod.mapper()
    def map_func(ir):
        return ConfigFragment(name="dummy", data={"programs.dummy.enable": True})

    console = Console(quiet=True)
    script = NixScribe(console=console, modules={"test.dummy": dummy_mod})
    script.run()

    ir_file = args.output_path / "scan-ir.json"
    assert ir_file.exists()

    data = json.loads(ir_file.read_text(encoding="utf-8"))
    assert "test.dummy" in data
    assert data["test.dummy"]["option"] == "value"
    assert data["test.dummy"]["password"] == "supersecret"

    # Clean up args
    args.dump_ir = False


def test_nixscribe_print_summary(tmp_path):
    from io import StringIO

    from nix_scribe.arguments import args
    from nix_scribe.lib.option_block import ConfigFragment
    from nix_scribe.lib.packages import (
        DiscoveredPackage,
        InstallReason,
        PackageState,
        ResolvedPackage,
    )

    args.output_path = tmp_path / "nix-config"
    args.log_file = tmp_path / "nix-config" / "nix-scribe.log"
    args.log_file.parent.mkdir(parents=True, exist_ok=True)
    args.log_file.write_text("log content", encoding="utf-8")

    mod1 = Module("test.configured")

    @mod1.scanner()
    def scan1(context):
        return {"enable": True}

    @mod1.mapper()
    def map1(ir):
        return ConfigFragment(name="configured", data={"configured.enable": True})

    mod2 = Module("test.skipped")

    @mod2.scanner()
    def scan2(context):
        return {}

    @mod2.mapper()
    def map2(ir):
        return None

    string_io = StringIO()
    console = Console(file=string_io, force_terminal=False, color_system=None)

    script = NixScribe(
        console=console,
        modules={"test.configured": mod1, "test.skipped": mod2},
    )

    pkg = ResolvedPackage(
        "curl", DiscoveredPackage("curl", "arch", InstallReason.EXPLICIT)
    )
    script.context.packages = PackageState(packages=[pkg])
    script.context.packages.claim("curl", by="test.configured")

    script.results["test.configured"].map_data = map1({})
    script.results["test.skipped"].map_data = map2({})

    script._print_summary(total_duration=1.23)

    output = string_io.getvalue()
    assert "nix-scribe generation complete" in output
    assert "Target OS:" in output
    assert "1 configured" in output
    assert "test" in output
    assert "configured" in output
    assert "1 skipped" in output
    assert "Packages:" in output
    assert "1 resolved" in output
    assert "1 claimed" in output
    assert "Artifacts:" in output
    assert "nix-scribe.log" in output


def test_nixscribe_build_modules_tree():
    console = Console(quiet=True)
    script = NixScribe(console=console, modules={})

    assert script._build_modules_tree([]) == "[yellow]0 configured[/yellow]"

    tree = script._build_modules_tree(
        [
            "boot.kernel",
            "boot.loader.systemd-boot",
            "networking.networkmanager",
            "users.users",
        ]
    )
    assert "4 configured" in tree.label
    assert len(tree.children) == 3  # boot, networking, users


def test_nixscribe_build_artifacts_tree():
    console = Console(quiet=True)
    script = NixScribe(console=console, modules={})

    assert script._build_artifacts_tree([]) == "[dim]None[/dim]"

    tree = script._build_artifacts_tree(
        [
            "configuration.nix",
            "networking/default.nix",
            "networking/networkmanager.nix",
            "users/default.nix",
        ]
    )
    assert "4 files generated" in tree.label
    assert len(tree.children) == 3  # configuration.nix, networking, users
