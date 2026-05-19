from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.programs.git import git


def test_git_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    context = SystemContext(tmp_path)
    assert git.scan
    ir = git.scan(context)

    assert ir["enable"] is True
    assert "lfs" not in ir
    assert ir["promptEnable"] is False


def test_git_scanner_lfs(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()
    (tmp_path / "usr/bin/git-lfs").touch()

    context = SystemContext(tmp_path)
    assert git.scan
    ir = git.scan(context)

    assert ir["lfs"]["enable"] is True


def test_git_scanner_config(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/gitconfig").write_text("""
[user]
    name = Test User
    email = test@example.com
[core]
    editor = vim
""")

    context = SystemContext(tmp_path)
    assert git.scan
    ir = git.scan(context)

    assert ir["config"]["user"]["name"] == "Test User"
    assert ir["config"]["core"]["editor"] == "vim"


def test_git_scanner_prompt(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    (tmp_path / "etc").mkdir()

    # PS1 call to __git_ps1
    (tmp_path / "etc/bashrc").write_text(r'PS1="\u@\h \W$(__git_ps1 \" (%s)\")\$ "')
    context = SystemContext(tmp_path)
    assert git.scan
    assert git.scan(context)["promptEnable"] is True

    # source git-prompt.sh
    (tmp_path / "etc/bashrc").write_text("source /usr/lib/git-core/git-sh-prompt")
    assert git.scan(context)["promptEnable"] is True


def test_git_mapper_basic():
    assert git.map
    mapper = git.map

    ir: dict[str, Any] = {"enable": True, "promptEnable": False}
    block = mapper(ir)
    assert block is not None and isinstance(block, SimpleOptionBlock)
    assert block.data["programs.git"]["enable"] is True
    assert "lfs.enable" not in block.data["programs.git"]


def test_git_mapper_full():
    assert git.map
    mapper = git.map

    ir = {
        "enable": True,
        "lfs": {"enable": True, "enablePureSSHTransfer": True},
        "promptEnable": True,
        "config": {"user": {"name": "Test"}},
    }
    block = mapper(ir)
    assert block is not None and isinstance(block, SimpleOptionBlock)

    git_config = block.data["programs.git"]
    assert git_config["enable"] is True
    assert git_config["lfs.enable"] is True
    assert git_config["lfs.enablePureSSHTransfer"] is True
    assert git_config["prompt.enable"] is True
    assert git_config["config"]["user"]["name"] == "Test"
