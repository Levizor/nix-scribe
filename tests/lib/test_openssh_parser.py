from nix_scribe.lib.parsers.openssh import parse_openssh_config


def test_parse_openssh_basic():
    content = """
    # Sample sshd_config
    Port 22
    Port 2222
    PermitRootLogin prohibit-password
    PasswordAuthentication no
    X11Forwarding yes
    HostKey /etc/ssh/ssh_host_rsa_key
    HostKey /etc/ssh/ssh_host_ed25519_key
    Banner /etc/issue.net
    """
    parsed = parse_openssh_config(content)

    assert parsed["Port"] == [22, 2222]
    assert parsed["PermitRootLogin"] == "prohibit-password"
    assert parsed["PasswordAuthentication"] is False
    assert parsed["X11Forwarding"] is True
    assert parsed["HostKey"] == [
        "/etc/ssh/ssh_host_rsa_key",
        "/etc/ssh/ssh_host_ed25519_key",
    ]
    assert parsed["Banner"] == "/etc/issue.net"


def test_parse_openssh_equals_separator():
    content = """
    PermitRootLogin = yes
    PasswordAuthentication = false
    Port = 22
    """
    parsed = parse_openssh_config(content)

    assert parsed["PermitRootLogin"] is True
    assert parsed["PasswordAuthentication"] is False
    assert parsed["Port"] == [22]
