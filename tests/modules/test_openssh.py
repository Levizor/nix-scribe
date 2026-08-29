from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.services.openssh import map as map_openssh, scan as scan_openssh


def test_openssh_service_disabled(tmp_path):
    ctx = SystemContext(root=tmp_path)
    ir = scan_openssh(ctx)
    assert ir["enable"] is False

    fragment = map_openssh(ir)
    assert fragment is None


def test_openssh_service_enabled_with_config(tmp_path):
    ssh_dir = tmp_path / "etc" / "ssh"
    ssh_dir.mkdir(parents=True)
    sshd_config = ssh_dir / "sshd_config"
    sshd_config.write_text(
        "Port 2222\n"
        "PermitRootLogin prohibit-password\n"
        "PasswordAuthentication no\n"
        "HostKey /etc/ssh/ssh_host_ed25519_key\n"
    )

    ctx = SystemContext(root=tmp_path)
    ir = scan_openssh(ctx)

    assert ir["enable"] is True
    assert ir["ports"] == [2222]
    assert ir["settings"]["PermitRootLogin"] == "prohibit-password"
    assert ir["settings"]["PasswordAuthentication"] is False
    assert ir["hostKeys"] == [
        {"path": "/etc/ssh/ssh_host_ed25519_key", "type": "ed25519"}
    ]

    fragment = map_openssh(ir)
    assert fragment is not None
    assert fragment.name == "openssh"
    assert fragment["services.openssh"].value == {
        "enable": True,
        "ports": [2222],
        "hostKeys": [{"path": "/etc/ssh/ssh_host_ed25519_key", "type": "ed25519"}],
        "settings": {
            "PermitRootLogin": "prohibit-password",
            "PasswordAuthentication": False,
        },
    }


def test_openssh_service_config_directory(tmp_path):
    ssh_dir = tmp_path / "etc" / "ssh"
    config_d = ssh_dir / "sshd_config.d"
    config_d.mkdir(parents=True)

    (ssh_dir / "sshd_config").write_text("Port 22\n")
    (config_d / "custom.conf").write_text("X11Forwarding yes\nBanner /etc/issue\n")

    ctx = SystemContext(root=tmp_path)
    ir = scan_openssh(ctx)

    assert ir["enable"] is True
    assert ir["ports"] == [22]
    assert ir["settings"]["X11Forwarding"] is True
    assert ir["settings"]["Banner"] == "/etc/issue"
