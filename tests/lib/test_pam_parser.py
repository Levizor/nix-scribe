from nix_scribe.lib.parsers.pam import parse_pam

MOCK_PAM_SUDO = """
# /etc/pam.d/sudo - PAM configuration for sudo
auth       required   pam_env.so
auth       sufficient pam_ssh_agent_auth.so file=~/.ssh/authorized_keys
auth       required   pam_unix.so nullok try_first_pass
account    required   pam_unix.so
session    required   pam_limits.so
"""


def test_parse_pam_empty():
    res = parse_pam("")
    assert res["rules"] == []
    assert res["has_ssh_agent_auth"] is False
    assert res["raw_lines"] == []


def test_parse_pam_ssh_agent_auth():
    res = parse_pam(MOCK_PAM_SUDO)
    assert res["has_ssh_agent_auth"] is True
    assert len(res["rules"]) == 5
    assert res["rules"][1]["module"] == "pam_ssh_agent_auth.so"
    assert res["rules"][1]["args"] == ["file=~/.ssh/authorized_keys"]
    assert len(res["raw_lines"]) == 5


def test_parse_pam_modules():
    content = """
    auth optional pam_kwallet5.so
    auth optional pam_gnupg.so
    auth sufficient pam_u2f.so
    auth sufficient pam_yubico.so
    auth required pam_mount.so
    """
    res = parse_pam(content)
    assert res["has_kwallet"] is True
    assert res["has_gnupg"] is True
    assert res["has_u2f"] is True
    assert res["has_yubico"] is True
    assert res["has_mount"] is True
