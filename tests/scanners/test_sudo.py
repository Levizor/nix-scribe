from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.security.sudo import Sudo
from nix_scribe.scanners.security.sudo import sudo

SUDOERS_CONTENT = """
Defaults env_reset
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults env_keep += "TERMINFO TERMINFO_DIRS"
root ALL=(ALL:ALL) ALL
alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
"""

WHEEL_NOPASSWD_CONTENT = "%wheel ALL=(ALL:ALL) NOPASSWD: ALL\n"


def test_sudo_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert sudo.scan(context) is None


def test_sudo_scanner_filesystem(tmp_path):
    assert sudo.scan
    etc_path = tmp_path / "etc"
    etc_path.mkdir()
    (etc_path / "sudoers").write_text(SUDOERS_CONTENT)

    sudoers_d = etc_path / "sudoers.d"
    sudoers_d.mkdir()
    (sudoers_d / "10-wheel").write_text(WHEEL_NOPASSWD_CONTENT)

    usr_bin = tmp_path / "usr/bin"
    usr_bin.mkdir(parents=True)
    sudo_bin = usr_bin / "sudo"
    sudo_bin.touch()
    sudo_bin.chmod(0o4755)

    context = SystemContext(tmp_path)
    mod = sudo.scan(context)

    assert isinstance(mod, Sudo)
    assert mod.enable is True
    assert mod.wheelNeedsPassword is False
    assert mod.keepTerminfo is True
    assert mod.execWheelOnly is False
    assert "alice ALL=(ALL) NOPASSWD" in mod.extraConfig
    assert mod.resolve_claims() == {"sudo"}

    fragment = mod.to_nix_fragment()
    data = fragment["security.sudo"].value
    assert "enable" not in data
    assert data["wheelNeedsPassword"] is False
    assert "keepTerminfo" not in data
    assert "execWheelOnly" not in data
    assert "TERMINFO" not in data["extraConfig"]
    assert "alice ALL=(ALL) NOPASSWD" in data["extraConfig"]


def test_sudo_scanner_exec_wheel_only(tmp_path):
    etc_path = tmp_path / "etc"
    etc_path.mkdir()
    (etc_path / "sudoers").write_text("root ALL=(ALL:ALL) ALL\n")

    usr_bin = tmp_path / "usr/bin"
    usr_bin.mkdir(parents=True)
    sudo_bin = usr_bin / "sudo"
    sudo_bin.touch()
    sudo_bin.chmod(0o4750)

    context = SystemContext(tmp_path)
    mod = sudo.scan(context)

    assert isinstance(mod, Sudo)
    assert mod.execWheelOnly is True
    assert mod.keepTerminfo is False

    fragment = mod.to_nix_fragment()
    assert fragment["security.sudo"].value["keepTerminfo"] is False
