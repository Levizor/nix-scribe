from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.bash import Bash
from nix_scribe.scanners.programs.bash import bash


def test_bash_scanner_not_found(tmp_path):
    context = SystemContext(tmp_path)
    assert bash.scan(context) is None


def test_bash_scanner_with_files(tmp_path):
    (tmp_path / "bin").mkdir(parents=True)
    (tmp_path / "bin/bash").touch()
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/profile").write_text("export PATH=/usr/local/bin:$PATH")
    (tmp_path / "etc/bash.bashrc").write_text(
        "alias ll='ls -la'\nPS1='\\u@\\h:\\w\\$ '\necho hello\n"
    )
    (tmp_path / "etc/bash_logout").write_text("clear")

    context = SystemContext(tmp_path)
    mod = bash.scan(context)

    assert isinstance(mod, Bash)
    assert mod.enable is True
    assert mod.loginShellInit == "export PATH=/usr/local/bin:$PATH"
    assert mod.logout == "clear"
    assert mod.shellAliases == {"ll": "ls -la"}
    assert mod.promptInit == ""
    assert "echo hello" in mod.interactiveShellInit
    assert mod.resolve_claims() == {"bash"}

    fragment = mod.to_nix_fragment()
    data = fragment["programs.bash"].value
    assert data["enable"] is True
    assert data["shellAliases"] == {"ll": "ls -la"}
    assert data["promptInit"] == ""
