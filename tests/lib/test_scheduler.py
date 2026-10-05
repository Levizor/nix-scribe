from rich.console import Console

from nix_scribe.lib.registry import Module, ModulePhase
from nix_scribe.lib.scheduler import ModuleScheduler
from nix_scribe.nixscribe import NixScribe


def test_module_phase_values_and_ordering():
    assert ModulePhase.EARLY == 10
    assert ModulePhase.NORMAL == 50
    assert ModulePhase.LATE == 100

    assert ModulePhase.EARLY < ModulePhase.NORMAL < ModulePhase.LATE


def test_module_default_and_custom_phase():
    mod_default = Module("test.default")
    assert mod_default.phase == ModulePhase.NORMAL

    mod_early = Module("test.early", phase=ModulePhase.EARLY)
    assert mod_early.phase == ModulePhase.EARLY

    mod_late = Module("test.late", phase=ModulePhase.LATE)
    assert mod_late.phase == ModulePhase.LATE


def test_module_scheduler_empty():
    assert ModuleScheduler.schedule({}) == {}


def test_module_scheduler_phase_ordering():
    late_mod = Module("environment.systemPackages", phase=ModulePhase.LATE)
    normal_mod_b = Module("services.openssh", phase=ModulePhase.NORMAL)
    normal_mod_a = Module("programs.zsh", phase=ModulePhase.NORMAL)
    early_mod = Module("system.detection", phase=ModulePhase.EARLY)

    unordered = {
        "environment.systemPackages": late_mod,
        "services.openssh": normal_mod_b,
        "programs.zsh": normal_mod_a,
        "system.detection": early_mod,
    }

    scheduled = ModuleScheduler.schedule(unordered)

    assert list(scheduled.keys()) == [
        "system.detection",
        "programs.zsh",
        "services.openssh",
        "environment.systemPackages",
    ]


def test_nixscribe_schedules_modules_on_init():
    late_mod = Module("environment.systemPackages", phase=ModulePhase.LATE)
    normal_mod = Module("programs.git", phase=ModulePhase.NORMAL)
    early_mod = Module("boot.loader", phase=ModulePhase.EARLY)

    modules = {
        "environment.systemPackages": late_mod,
        "programs.git": normal_mod,
        "boot.loader": early_mod,
    }

    scribe = NixScribe(console=Console(quiet=True), modules=modules)

    expected_order = ["boot.loader", "programs.git", "environment.systemPackages"]
    assert list(scribe.modules.keys()) == expected_order
    assert list(scribe.results.keys()) == expected_order
