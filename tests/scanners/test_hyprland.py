from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.hyprland import Hyprland
from nix_scribe.scanners.programs.hyprland import hyprland


def test_hyprland_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    assert hyprland.scan(context) is None


def test_hyprland_scanner_found(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/Hyprland").touch()

    context = SystemContext(tmp_path)
    mod = hyprland.scan(context)

    assert isinstance(mod, Hyprland)
    assert mod.enable is True
    assert mod.resolve_claims() == {"hyprland"}

    fragment = mod.to_nix_fragment()
    assert fragment["programs.hyprland"].value == {"enable": True}
