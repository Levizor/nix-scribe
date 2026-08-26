from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.security.pam import pam

MOCK_PAM_FILE = """
auth required pam_unix.so
auth sufficient pam_ssh_agent_auth.so file=/etc/ssh/authorized_keys
auth optional pam_kwallet5.so
"""


def test_pam_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    ir = pam.scan(context)
    assert ir == {}


def test_pam_scanner_with_files(tmp_path):
    pam_dir = tmp_path / "etc/pam.d"
    pam_dir.mkdir(parents=True)
    (pam_dir / "sudo").write_text(MOCK_PAM_FILE)
    (pam_dir / "login").write_text("auth required pam_mount.so\n")

    context = SystemContext(tmp_path)
    ir = pam.scan(context)

    assert ir["sshAgentAuth"] is True
    assert ir["mount"] is True
    assert "sudo" in ir["services"]
    assert ir["services"]["sudo"]["kwallet"]["enable"] is True


def test_pam_mapper():
    assert pam.map
    mock_ir = {
        "sshAgentAuth": True,
        "mount": True,
        "u2f": True,
        "services": {"sudo": {"kwallet": {"enable": True}, "u2f": {"enable": True}}},
    }

    block = pam.map(mock_ir)
    assert isinstance(block, ConfigFragment)
    data = block["security.pam"]
    assert data["sshAgentAuth.enable"] is True
    assert data["u2f.enable"] is True
    assert data["mount.enable"] is True
    assert data["services"]["sudo"]["kwallet"]["enable"] is True
    assert data["services"]["sudo"]["u2f"]["enable"] is True


def test_pam_mapper_empty():
    assert pam.map(None) is None
    assert pam.map({}) is None
