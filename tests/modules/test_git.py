from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.programs.git import GitMapper, GitScanner


def test_git_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    context = SystemContext(tmp_path)
    scanner = GitScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert "lfs" not in ir
    assert ir["promptEnable"] is False


def test_git_scanner_lfs(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()
    (tmp_path / "usr/bin/git-lfs").touch()

    context = SystemContext(tmp_path)
    scanner = GitScanner()
    ir = scanner.scan(context)

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
    scanner = GitScanner()
    ir = scanner.scan(context)

    assert ir["config"]["user"]["name"] == "Test User"
    assert ir["config"]["core"]["editor"] == "vim"


def test_git_scanner_prompt(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    (tmp_path / "etc").mkdir()

    # PS1 call to __git_ps1
    (tmp_path / "etc/bashrc").write_text(r'PS1="\u@\h \W$(__git_ps1 \" (%s)\")\$ "')
    context = SystemContext(tmp_path)
    scanner = GitScanner()
    assert scanner.scan(context)["promptEnable"] is True

    # source git-prompt.sh
    (tmp_path / "etc/bashrc").write_text("source /usr/lib/git-core/git-sh-prompt")
    assert scanner.scan(context)["promptEnable"] is True


def test_git_mapper_basic():
    mapper = GitMapper()

    ir: dict[str, Any] = {"enable": True, "promptEnable": False}
    block = mapper.map(ir)
    assert block is not None
    assert block.data["programs.git"]["enable"] is True
    assert "lfs.enable" not in block.data["programs.git"]


def test_git_mapper_full():
    mapper = GitMapper()

    ir = {
        "enable": True,
        "lfs": {"enable": True, "enablePureSSHTransfer": True},
        "promptEnable": True,
        "config": {"user": {"name": "Test"}},
    }
    block = mapper.map(ir)
    assert block is not None

    git_config = block.data["programs.git"]
    assert git_config["enable"] is True
    assert git_config["lfs.enable"] is True
    assert git_config["lfs.enablePureSSHTransfer"] is True
    assert git_config["prompt.enable"] is True
    assert git_config["config"]["user"]["name"] == "Test"
