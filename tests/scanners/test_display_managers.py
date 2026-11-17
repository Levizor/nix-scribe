from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_fragment import NixFragment
from nix_scribe.modules.nixos.services.displayManager.cosmic_greeter import (
    CosmicGreeter,
)
from nix_scribe.modules.nixos.services.displayManager.gdm import Gdm
from nix_scribe.modules.nixos.services.displayManager.plasma_login_manager import (
    PlasmaLoginManager,
)
from nix_scribe.modules.nixos.services.displayManager.sddm import Sddm
from nix_scribe.scanners.services.displayManager.cosmic_greeter import (
    cosmic_greeter,
)
from nix_scribe.scanners.services.displayManager.gdm import gdm
from nix_scribe.scanners.services.displayManager.plasma_login_manager import (
    plasma_login_manager,
)
from nix_scribe.scanners.services.displayManager.sddm import sddm


def test_cosmic_greeter_scanner(tmp_path, monkeypatch):
    context = SystemContext(tmp_path)
    monkeypatch.setattr(context.systemctl, "is_enabled", lambda _: False)
    assert cosmic_greeter.scan(context) is None

    monkeypatch.setattr(
        context.systemctl,
        "is_enabled",
        lambda unit: unit == "cosmic-greeter-daemon",
    )
    mod = cosmic_greeter.scan(context)
    assert isinstance(mod, CosmicGreeter)
    assert mod.enable is True
    assert mod.resolve_claims() == {"cosmic-greeter"}

    fragment = mod.to_nix_fragment()
    assert isinstance(fragment, NixFragment)
    assert fragment["services.displayManager.cosmic-greeter"]["enable"] is True


def test_gdm_scanner_disabled(tmp_path, monkeypatch):
    context = SystemContext(tmp_path)
    monkeypatch.setattr(context.systemctl, "is_enabled", lambda _: False)
    assert gdm.scan(context) is None


def test_gdm_scanner_configured(tmp_path, monkeypatch):
    custom_conf = (
        "[daemon]\n"
        "WaylandEnable=false\n"
        "TimedLoginDelay=15\n"
        "AutomaticLoginEnable=true\n"
        "[debug]\n"
        "Enable=true\n"
        "[security]\n"
        "DisallowTCP=true\n"
    )
    gdm_dir = tmp_path / "etc/gdm"
    gdm_dir.mkdir(parents=True)
    (gdm_dir / "custom.conf").write_text(custom_conf)

    context = SystemContext(tmp_path)
    monkeypatch.setattr(
        context.systemctl,
        "is_enabled",
        lambda unit: unit == "gdm",
    )

    mod = gdm.scan(context)
    assert isinstance(mod, Gdm)
    assert mod.enable is True
    assert mod.wayland is False
    assert mod.autoLogin_delay == 15
    assert mod.debug is True
    assert mod.settings == {
        "daemon": {"AutomaticLoginEnable": True},
        "security": {"DisallowTCP": True},
    }
    assert mod.resolve_claims() == {"gdm"}

    fragment = mod.to_nix_fragment()
    data = fragment["services.displayManager.gdm"]
    assert data["enable"] is True
    assert data["wayland"] is False
    assert data["autoLogin.delay"] == 15
    assert data["debug"] is True
    assert data["settings"]["daemon"]["AutomaticLoginEnable"] is True


def test_sddm_scanner_disabled(tmp_path, monkeypatch):
    context = SystemContext(tmp_path)
    monkeypatch.setattr(context.systemctl, "is_enabled", lambda _: False)
    assert sddm.scan(context) is None


def test_sddm_scanner_configured(tmp_path, monkeypatch):
    sddm_conf = (
        "[General]\n"
        "DisplayServer=wayland\n"
        "Numlock=on\n"
        "HaltCommand=/usr/bin/systemctl poweroff\n"
        "[Theme]\n"
        "Current=breeze\n"
        "CursorTheme=breeze_cursors\n"
    )
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir(parents=True)
    (etc_dir / "sddm.conf").write_text(sddm_conf)

    context = SystemContext(tmp_path)
    monkeypatch.setattr(
        context.systemctl,
        "is_enabled",
        lambda unit: unit == "sddm",
    )

    mod = sddm.scan(context)
    assert isinstance(mod, Sddm)
    assert mod.enable is True
    assert mod.wayland_enable is True
    assert mod.autoNumlock is True
    assert mod.theme == "breeze"
    assert mod.settings == {
        "General": {"HaltCommand": "/usr/bin/systemctl poweroff"},
        "Theme": {"CursorTheme": "breeze_cursors"},
    }
    assert mod.resolve_claims() == {
        "kdePackages.sddm",
        "kdePackages.sddm-unwrapped",
    }

    fragment = mod.to_nix_fragment()
    data = fragment["services.displayManager.sddm"]
    assert data["enable"] is True
    assert data["wayland.enable"] is True
    assert data["autoNumlock"] is True
    assert data["theme"] == "breeze"
    assert data["settings"]["Theme"]["CursorTheme"] == "breeze_cursors"


def test_plasma_login_manager_scanner_disabled(tmp_path, monkeypatch):
    context = SystemContext(tmp_path)
    monkeypatch.setattr(context.systemctl, "is_enabled", lambda _: False)
    assert plasma_login_manager.scan(context) is None


def test_plasma_login_manager_scanner_configured(tmp_path, monkeypatch):
    plasma_conf = "[General]\nTheme=default\n"
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir(parents=True, exist_ok=True)
    (etc_dir / "plasmalogin.conf").write_text(plasma_conf)

    context = SystemContext(tmp_path)
    monkeypatch.setattr(
        context.systemctl,
        "is_enabled",
        lambda unit: unit == "plasmalogin",
    )

    mod = plasma_login_manager.scan(context)
    assert isinstance(mod, PlasmaLoginManager)
    assert mod.enable is True
    assert mod.settings == {"General": {"Theme": "default"}}
    assert mod.resolve_claims() == {"kdePackages.plasma-login-manager"}

    fragment = mod.to_nix_fragment()
    data = fragment["services.displayManager.plasma-login-manager"]
    assert data["enable"] is True
    assert data["settings"]["General"]["Theme"] == "default"
