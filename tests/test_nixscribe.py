from rich.console import Console

from nix_scribe.lib.registry import Scanner
from nix_scribe.nixscribe import NixScribe


def test_nixscribe_injection():
    console = Console(quiet=True)
    dummy_module = Scanner("test.dummy")
    modules = {"test.dummy": dummy_module}

    script = NixScribe(console=console, modules=modules)

    assert script.modules == modules
    assert "test.dummy" in script.results
    assert script.results["test.dummy"] is None
    assert script.fragments["test.dummy"] is None


def test_nixscribe_scan_module_claims_packages():
    from nix_scribe.lib.nix_module import NixModule, option
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

    class GitContract(NixModule, prefix="programs.git", claims={"git"}):
        enable: bool | None = option()

    mod = Scanner("programs.git")

    @mod.scanner()
    def scan(context) -> GitContract:
        return GitContract(enable=True)

    script = NixScribe(console=console, modules={"programs.git": mod})
    script.context.packages = PackageState(packages=[git_pkg, curl_pkg])

    assert script.context.packages.unclaimed == [git_pkg, curl_pkg]

    script._scan_module(mod)

    assert script.fragments["programs.git"] is not None
    assert script.context.packages.is_claimed("git")
    assert script.context.packages.claimed_by("git") == "programs.git"
    assert script.context.packages.unclaimed == [curl_pkg]


def test_nixscribe_system_packages_claims_integration():
    from nix_scribe.lib.packages import (
        DiscoveredPackage,
        InstallReason,
        PackageState,
        ResolvedPackage,
    )
    from nix_scribe.modules.nixos.programs.git import Git
    from nix_scribe.scanners.environment.system_packages import system_packages

    console = Console(quiet=True)
    git_pkg = ResolvedPackage(
        "git", DiscoveredPackage("git", "debian", InstallReason.EXPLICIT)
    )
    curl_pkg = ResolvedPackage(
        "curl", DiscoveredPackage("curl", "debian", InstallReason.EXPLICIT)
    )

    git_mod = Scanner("programs.git")

    @git_mod.scanner()
    def scan_git(context) -> Git:
        return Git(enable=True)

    script = NixScribe(
        console=console,
        modules={
            "programs.git": git_mod,
            "environment.system_packages": system_packages,
        },
    )
    script.context.packages = PackageState(packages=[git_pkg, curl_pkg])

    # Scan phase
    for scanner in script.modules.values():
        script._scan_module(scanner)

    sys_frag = script.fragments["environment.system_packages"]
    assert sys_frag is not None
    rendered_options = sys_frag.options
    assert "environment" in rendered_options
    # Only curl should be in environment.systemPackages because git was claimed during scan
    assert script.context.packages.is_claimed("git")
    assert not script.context.packages.is_claimed("curl")

    from nix_scribe.lib.nix_writer import NixWriter
    from nix_scribe.lib.nixfile import NixFile

    nix_file = NixFile("configuration")
    nix_file.add_fragment(sys_frag)
    writer = NixWriter()
    nix_file.render(writer)
    output = writer.gettext()

    assert "curl" in output
    assert "git" not in output

    asset = next(iter(sys_frag.assets))
    assert "Claimed packages:" in asset.content
    assert "git # from debian:git (claimed by programs.git)" in asset.content


def test_nixscribe_run_progress_and_debug_logging(tmp_path, caplog):
    import logging

    from nix_scribe.cli.arguments import args
    from nix_scribe.lib.nix_module import NixModule, option

    args.output_path = tmp_path / "nix-config"

    class DummyContract(NixModule, prefix="programs.dummy"):
        enable: bool | None = option()

    dummy_mod = Scanner("test.dummy")

    @dummy_mod.scanner()
    def scan(context) -> DummyContract:
        return DummyContract(enable=True)

    console = Console(quiet=True)
    script = NixScribe(console=console, modules={"test.dummy": dummy_mod})

    with caplog.at_level(logging.DEBUG):
        script.run()

    # Per-module messages are logged at DEBUG level
    assert "Scanned test.dummy" in caplog.text

    # Milestone messages are logged at INFO level
    assert "Starting nix-scribe system scan..." in caplog.text
    assert "Finished system scan in" in caplog.text
    assert "Writing configuration..." in caplog.text
    assert (tmp_path / "nix-config" / "configuration.nix").exists()


def test_nixscribe_scan_module_elevation_pause():
    from unittest.mock import MagicMock

    from nix_scribe.lib.context import ElevationRequest

    dummy_mod = Scanner("test.restricted")

    @dummy_mod.scanner()
    def scan(context):
        raise ElevationRequest("/etc/shadow", "Requires root")

    console = Console(quiet=True)
    script = NixScribe(console=console, modules={"test.restricted": dummy_mod})

    mock_progress = MagicMock()
    script._prompt_for_sudo = MagicMock(return_value=False)

    script._scan_module(dummy_mod, progress=mock_progress)

    # Progress bar was stopped for prompt and resumed
    mock_progress.stop.assert_called_once()
    mock_progress.start.assert_called_once()
    assert script.results["test.restricted"] is None


def test_nixscribe_run_dump_ir(tmp_path):
    import json

    from nix_scribe.cli.arguments import args
    from nix_scribe.lib.nix_module import NixModule, option

    args.output_path = tmp_path / "nix-config"
    args.dump_ir = True

    class DummyContract(NixModule, prefix="programs.dummy"):
        option_val: str | None = option("option")
        password: str | None = option()

    dummy_mod = Scanner("test.dummy")

    @dummy_mod.scanner()
    def scan(context) -> DummyContract:
        return DummyContract(option_val="value", password="supersecret")

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

    from nix_scribe.cli.arguments import args
    from nix_scribe.lib.nix_fragment import NixFragment, NixValue
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

    mod1 = Scanner("test.configured")
    mod2 = Scanner("test.skipped")

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

    script.fragments["test.configured"] = NixFragment(
        name="configured", options={"configured.enable": NixValue(True)}
    )
    script.fragments["test.skipped"] = None

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


def test_nixscribe_single_stage_nix_module(tmp_path):
    import json

    from nix_scribe.cli.arguments import args
    from nix_scribe.lib.asset import Asset
    from nix_scribe.lib.nix_fragment import NixFragment
    from nix_scribe.lib.nix_module import NixModule, option
    from nix_scribe.lib.packages import (
        DiscoveredPackage,
        InstallReason,
        PackageState,
        ResolvedPackage,
    )
    from nix_scribe.lib.registry import Scanner
    from nix_scribe.scanners.environment.system_packages import system_packages

    args.output_path = tmp_path / "nix-out"
    args.dump_ir = True

    class GitModule(NixModule, prefix="programs.git", claims={"git"}):
        enable: bool | None = option()
        lfs_enable: bool | None = option(path="lfs.enable", claims={"git-lfs"})

    git_scanner = Scanner("programs.git", description="Git configuration")

    @git_scanner.scanner()
    def scan_git(context) -> GitModule | None:
        mod = GitModule(enable=True, lfs_enable=True)
        mod.add_asset(Asset("git-info.txt", "git asset"))
        return mod

    git_pkg = ResolvedPackage(
        "git", DiscoveredPackage("git", "debian", InstallReason.EXPLICIT)
    )
    lfs_pkg = ResolvedPackage(
        "git-lfs", DiscoveredPackage("git-lfs", "debian", InstallReason.EXPLICIT)
    )
    curl_pkg = ResolvedPackage(
        "curl", DiscoveredPackage("curl", "debian", InstallReason.EXPLICIT)
    )

    console = Console(quiet=True)
    script = NixScribe(
        console=console,
        modules={
            "programs.git": git_scanner,
            "environment.system_packages": system_packages,
        },
    )
    script.context.packages = PackageState(packages=[git_pkg, lfs_pkg, curl_pkg])

    try:
        script.run()

        git_mod = script.results["programs.git"]
        git_frag = script.fragments["programs.git"]
        assert isinstance(git_mod, GitModule)
        assert isinstance(git_frag, NixFragment)
        assert git_frag.description == "Git configuration"
        assert len(git_frag.assets) == 1

        # Claims registered immediately during scan
        assert script.context.packages.is_claimed("git")
        assert script.context.packages.is_claimed("git-lfs")
        assert not script.context.packages.is_claimed("curl")

        ir_data = json.loads((args.output_path / "scan-ir.json").read_text())
        assert ir_data["programs.git"] == {"enable": True, "lfs.enable": True}
    finally:
        args.dump_ir = False


def test_nixscribe_empty_module_discarded_by_engine():
    from nix_scribe.lib.nix_module import NixModule, option
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

    class EmptyContract(NixModule, prefix="programs.empty", claims={"git"}):
        enable: bool = option()
        unconfigured: str = option()

    empty_mod = Scanner("programs.empty")

    @empty_mod.scanner()
    def scan(context) -> EmptyContract:
        # Scanner returns contract instance without populating options
        return EmptyContract()

    script = NixScribe(console=console, modules={"programs.empty": empty_mod})
    script.context.packages = PackageState(packages=[git_pkg])

    script._scan_module(empty_mod)

    # Empty module should be cleanly discarded and not claim packages
    assert script.results["programs.empty"] is None
    assert script.fragments["programs.empty"] is None
    assert not script.context.packages.is_claimed("git")
