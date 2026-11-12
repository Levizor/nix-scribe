from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.zsh import Zsh
from nix_scribe.scanners.programs.zsh import zsh


def test_zsh_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    assert zsh.scan(context) is None


def test_zsh_scanner_found(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/zsh").touch()

    context = SystemContext(tmp_path)
    mod = zsh.scan(context)

    assert isinstance(mod, Zsh)
    assert mod.enable is True
    assert mod.resolve_claims() == {"zsh"}

    fragment = mod.to_nix_fragment()
    assert fragment["programs.zsh"].value == {"enable": True}
