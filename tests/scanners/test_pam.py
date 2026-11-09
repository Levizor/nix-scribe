from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.security.pam import Pam
from nix_scribe.scanners.security.pam import pam

MOCK_PAM_FILE = """
auth required pam_unix.so
auth sufficient pam_ssh_agent_auth.so file=/etc/ssh/authorized_keys
auth optional pam_kwallet5.so
"""


def test_pam_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert pam.scan(context) is None


def test_pam_scanner_with_files(tmp_path):
    pam_dir = tmp_path / "etc/pam.d"
    pam_dir.mkdir(parents=True)
    (pam_dir / "sudo").write_text(MOCK_PAM_FILE)
    (pam_dir / "login").write_text("auth required pam_mount.so\n")

    context = SystemContext(tmp_path)
    mod = pam.scan(context)

    assert isinstance(mod, Pam)
    assert mod.ssh_agent_auth_enable is True
    assert mod.mount_enable is True
    assert "sudo" in mod.services
    assert mod.services["sudo"].kwallet_enable is True

    fragment = mod.to_nix_fragment()
    data = fragment["security.pam"].value
    assert data["sshAgentAuth.enable"] is True
    assert data["mount.enable"] is True
    assert data["services"]["sudo"]["kwallet.enable"] is True
