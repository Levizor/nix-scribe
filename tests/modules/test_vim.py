import unittest.mock

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.programs.vim import vim


def test_vim_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()

    context = SystemContext(tmp_path)
    assert vim.scan
    ir = vim.scan(context)

    assert ir["enable"] is True
    assert ir["defaultEditor"] is False


def test_vim_scanner_default_editor_symlink(tmp_path):
    assert vim.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()
    (tmp_path / "usr/bin/editor").touch()

    context = SystemContext(tmp_path)

    with unittest.mock.patch.object(context, "readlink", return_value="/usr/bin/vim"):
        ir = vim.scan(context)

        assert ir["defaultEditor"] is True


def test_vim_scanner_default_editor_profile(tmp_path):
    assert vim.scan
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/vim").touch()

    (tmp_path / "etc").mkdir()

    (tmp_path / "etc/profile").write_text('export EDITOR="vim"')
    context = SystemContext(tmp_path)
    assert vim.scan(context)["defaultEditor"] is True

    (tmp_path / "etc/profile").write_text("EDITOR=vi")
    assert vim.scan(context)["defaultEditor"] is True

    (tmp_path / "etc/profile").write_text("export VISUAL=/usr/local/bin/vim")
    assert vim.scan(context)["defaultEditor"] is True

    (tmp_path / "etc/profile").write_text("export EDITOR=nano")
    assert vim.scan(context)["defaultEditor"] is False


def test_vim_mapper():
    assert vim.map
    mapper = vim.map

    # not enabled
    assert mapper({"enable": False}) is None

    # enabled not default
    block = mapper({"enable": True, "defaultEditor": False})
    assert block is not None and isinstance(block, ConfigFragment)
    assert block["programs.vim"]["enable"] is True
    assert "defaultEditor" not in block["programs.vim"]

    # enabled, default
    block = mapper({"enable": True, "defaultEditor": True})
    assert block is not None and isinstance(block, ConfigFragment)
    assert block["programs.vim"]["enable"] is True
    assert block["programs.vim"]["defaultEditor"] is True
