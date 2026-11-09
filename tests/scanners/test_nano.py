from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.nano import Nano
from nix_scribe.scanners.programs.nano import nano


def test_nano_scanner_basic(tmp_path):
    assert nano.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()

    context = SystemContext(tmp_path)
    mod = nano.scan(context)

    assert isinstance(mod, Nano)
    assert mod.enable is True
    assert mod.nanorc == ""
    assert mod.resolve_claims() == {"nano"}

    fragment = mod.to_nix_fragment()
    assert fragment["programs.nano"].value == {"enable": True}


def test_nano_scanner_not_found(tmp_path):
    assert nano.scan
    context = SystemContext(tmp_path)
    assert nano.scan(context) is None


def test_nano_scanner_with_nanorc(tmp_path):
    assert nano.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()

    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/nanorc").write_text("set tabsize 4")

    context = SystemContext(tmp_path)
    mod = nano.scan(context)

    assert isinstance(mod, Nano)
    assert mod.enable is True
    assert mod.nanorc == "set tabsize 4"

    fragment = mod.to_nix_fragment()
    assert fragment["programs.nano"].value == {
        "enable": True,
        "nanorc": "set tabsize 4",
    }


def test_nano_scanner_with_commented_nanorc(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/nano").touch()
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/nanorc").write_text("\n# comment only\n")

    context = SystemContext(tmp_path)
    mod = nano.scan(context)

    assert isinstance(mod, Nano)
    assert mod.nanorc == ""
    fragment = mod.to_nix_fragment()
    assert "nanorc" not in fragment["programs.nano"].value
