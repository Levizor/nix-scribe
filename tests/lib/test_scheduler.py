from rich.console import Console

from nix_scribe.lib.registry import Scanner, ScannerPhase
from nix_scribe.lib.scheduler import ScannerScheduler
from nix_scribe.nixscribe import NixScribe


def test_scanner_phase_values_and_ordering():
    assert ScannerPhase.EARLY == 10
    assert ScannerPhase.NORMAL == 50
    assert ScannerPhase.LATE == 100

    assert ScannerPhase.EARLY < ScannerPhase.NORMAL < ScannerPhase.LATE


def test_scanner_default_and_custom_phase():
    mod_default = Scanner("test.default")
    assert mod_default.phase == ScannerPhase.NORMAL

    mod_early = Scanner("test.early", phase=ScannerPhase.EARLY)
    assert mod_early.phase == ScannerPhase.EARLY

    mod_late = Scanner("test.late", phase=ScannerPhase.LATE)
    assert mod_late.phase == ScannerPhase.LATE


def test_scanner_scheduler_empty():
    assert ScannerScheduler.schedule({}) == {}


def test_scanner_scheduler_phase_ordering():
    late_mod = Scanner("environment.systemPackages", phase=ScannerPhase.LATE)
    normal_mod_b = Scanner("services.openssh", phase=ScannerPhase.NORMAL)
    normal_mod_a = Scanner("programs.zsh", phase=ScannerPhase.NORMAL)
    early_mod = Scanner("system.detection", phase=ScannerPhase.EARLY)

    unordered = {
        "environment.systemPackages": late_mod,
        "services.openssh": normal_mod_b,
        "programs.zsh": normal_mod_a,
        "system.detection": early_mod,
    }

    scheduled = ScannerScheduler.schedule(unordered)

    assert list(scheduled.keys()) == [
        "system.detection",
        "programs.zsh",
        "services.openssh",
        "environment.systemPackages",
    ]


def test_nixscribe_schedules_modules_on_init():
    late_mod = Scanner("environment.systemPackages", phase=ScannerPhase.LATE)
    normal_mod = Scanner("programs.git", phase=ScannerPhase.NORMAL)
    early_mod = Scanner("boot.loader", phase=ScannerPhase.EARLY)

    modules = {
        "environment.systemPackages": late_mod,
        "programs.git": normal_mod,
        "boot.loader": early_mod,
    }

    scribe = NixScribe(console=Console(quiet=True), modules=modules)

    expected_order = ["boot.loader", "programs.git", "environment.systemPackages"]
    assert list(scribe.modules.keys()) == expected_order
    assert list(scribe.results.keys()) == expected_order
