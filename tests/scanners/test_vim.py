import unittest.mock

from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.vim import Vim
from nix_scribe.scanners.programs.vim import vim


def test_vim_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    assert vim.scan(context) is None


def test_vim_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()

    context = SystemContext(tmp_path)
    assert vim.scan
    mod = vim.scan(context)

    assert isinstance(mod, Vim)
    assert mod.enable is True
    assert mod.defaultEditor is False
    assert mod.resolve_claims() == {"vim"}

    fragment = mod.to_nix_fragment()
    assert fragment["programs.vim"].value == {"enable": True}


def test_vim_scanner_default_editor_symlink(tmp_path):
    assert vim.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()
    (tmp_path / "usr/bin/editor").touch()

    context = SystemContext(tmp_path)

    with unittest.mock.patch.object(context, "readlink", return_value="/usr/bin/vim"):
        mod = vim.scan(context)

        assert isinstance(mod, Vim)
        assert mod.defaultEditor is True

        fragment = mod.to_nix_fragment()
        assert fragment["programs.vim"].value == {
            "enable": True,
            "defaultEditor": True,
        }


def test_vim_scanner_default_editor_profile(tmp_path):
    assert vim.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()

    (tmp_path / "etc").mkdir()

    (tmp_path / "etc/profile").write_text('export EDITOR="vim"')
    context = SystemContext(tmp_path)
    assert vim.scan(context).defaultEditor is True

    (tmp_path / "etc/profile").write_text("EDITOR=vi")
    assert vim.scan(context).defaultEditor is True

    (tmp_path / "etc/profile").write_text("export VISUAL=/usr/local/bin/vim")
    assert vim.scan(context).defaultEditor is True

    (tmp_path / "etc/profile").write_text("export EDITOR=nano")
    assert vim.scan(context).defaultEditor is False
