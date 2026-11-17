from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.git import Git
from nix_scribe.scanners.programs.git import git


def test_git_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    assert git.scan(context) is None


def test_git_scanner_basic(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    context = SystemContext(tmp_path)
    assert git.scan
    mod = git.scan(context)

    assert isinstance(mod, Git)
    assert mod.enable is True
    assert mod.lfs is None
    assert mod.prompt_enable is False
    assert mod.resolve_claims() == {"git"}


def test_git_scanner_lfs(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()
    (tmp_path / "usr/bin/git-lfs").touch()

    context = SystemContext(tmp_path)
    mod = git.scan(context)

    assert isinstance(mod, Git)
    assert mod.lfs is not None
    assert mod.lfs.enable is True
    assert mod.resolve_claims() == {"git", "git-lfs"}

    fragment = mod.to_nix_fragment()
    data = fragment["programs.git"].value
    assert data["enable"] is True
    assert data["lfs"]["enable"] is True


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
    mod = git.scan(context)

    assert isinstance(mod, Git)
    assert mod.config["user"]["name"] == "Test User"
    assert mod.config["core"]["editor"] == "vim"


def test_git_scanner_prompt(tmp_path):
    (tmp_path / "usr/bin").mkdir(parents=True)
    (tmp_path / "usr/bin/git").touch()

    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/bashrc").write_text(r'PS1="\u@\h \W$(__git_ps1 \" (%s)\")\$ "')
    context = SystemContext(tmp_path)
    mod = git.scan(context)
    assert isinstance(mod, Git)
    assert mod.prompt_enable is True

    (tmp_path / "etc/bashrc").write_text("source /usr/lib/git-core/git-sh-prompt")
    mod2 = git.scan(context)
    assert isinstance(mod2, Git)
    assert mod2.prompt_enable is True
