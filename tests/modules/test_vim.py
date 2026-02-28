import unittest.mock

from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.programs.vim import VimMapper, VimScanner


def test_vim_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()

    context = SystemContext(tmp_path)
    scanner = VimScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert ir["defaultEditor"] is False


def test_vim_scanner_default_editor_symlink(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()
    (tmp_path / "usr/bin/editor").touch()

    context = SystemContext(tmp_path)

    with unittest.mock.patch.object(context, "readlink", return_value="/usr/bin/vim"):
        scanner = VimScanner()
        ir = scanner.scan(context)

        assert ir["defaultEditor"] is True


def test_vim_scanner_default_editor_profile(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()

    (tmp_path / "etc").mkdir()

    (tmp_path / "etc/profile").write_text('export EDITOR="vim"')
    context = SystemContext(tmp_path)
    scanner = VimScanner()
    assert scanner.scan(context)["defaultEditor"] is True

    (tmp_path / "etc/profile").write_text("EDITOR=vi")
    assert scanner.scan(context)["defaultEditor"] is True

    (tmp_path / "etc/profile").write_text("export VISUAL=/usr/local/bin/vim")
    assert scanner.scan(context)["defaultEditor"] is True

    (tmp_path / "etc/profile").write_text("export EDITOR=nano")
    assert scanner.scan(context)["defaultEditor"] is False


def test_vim_mapper():
    mapper = VimMapper()

    # not enabled
    assert mapper.map({"enable": False}) is None

    # enabled not default
    block = mapper.map({"enable": True, "defaultEditor": False})
    assert block is not None
    assert block.data["programs.vim.enable"] is True
    assert "programs.vim.defaultEditor" not in block.data

    # enabled, default
    block = mapper.map({"enable": True, "defaultEditor": True})
    assert block is not None
    assert block.data["programs.vim.enable"] is True
    assert block.data["programs.vim.defaultEditor"] is True
