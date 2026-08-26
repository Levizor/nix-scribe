from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.security.sudo import sudo

SUDOERS_CONTENT = """
Defaults env_reset
Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults env_keep += "TERMINFO TERMINFO_DIRS"
root ALL=(ALL:ALL) ALL
alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
"""

WHEEL_NOPASSWD_CONTENT = "%wheel ALL=(ALL:ALL) NOPASSWD: ALL\n"


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
    ir = sudo.scan(context)

    assert ir["enable"] is True
    assert ir["wheelNeedsPassword"] is False
    assert ir["keepTerminfo"] is True
    assert ir["execWheelOnly"] is False
    assert len(ir["extraConfigLines"]) == 1
    assert "alice ALL=(ALL) NOPASSWD" in ir["extraConfigLines"][0]


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
    ir = sudo.scan(context)

    assert ir["execWheelOnly"] is True


def test_sudo_mapper():
    assert sudo.map
    mock_ir = {
        "enable": True,
        "wheelNeedsPassword": False,
        "execWheelOnly": True,
        "keepTerminfo": True,
        "extraConfigLines": ["bob ALL=(ALL) ALL"],
    }

    block = sudo.map(mock_ir)

    assert isinstance(block, ConfigFragment)
    data = block["security.sudo"]

    assert data["enable"] is True
    assert data["wheelNeedsPassword"] is False
    assert data["execWheelOnly"] is True
    assert data["keepTerminfo"] is True
    assert data["extraConfig"] == "bob ALL=(ALL) ALL"
