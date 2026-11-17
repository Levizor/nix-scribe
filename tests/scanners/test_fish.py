from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.fish import Fish
from nix_scribe.scanners.programs.fish import fish


def test_fish_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    assert fish.scan(context) is None


def test_fish_scanner_found(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/fish").touch()

    context = SystemContext(tmp_path)
    mod = fish.scan(context)

    assert isinstance(mod, Fish)
    assert mod.enable is True
    assert mod.resolve_claims() == {"fish"}

    fragment = mod.to_nix_fragment()
    assert fragment["programs.fish"].value == {"enable": True}
