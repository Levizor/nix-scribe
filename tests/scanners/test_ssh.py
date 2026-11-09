from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.programs.ssh import Ssh
from nix_scribe.scanners.programs.ssh import scan as scan_ssh


def test_ssh_client_disabled(tmp_path):
    ctx = SystemContext(root=tmp_path)
    assert scan_ssh(ctx) is None


def test_ssh_client_enabled_with_config(tmp_path):
    ssh_dir = tmp_path / "etc" / "ssh"
    ssh_dir.mkdir(parents=True)
    ssh_config = ssh_dir / "ssh_config"
    ssh_config.write_text("ForwardX11 yes\nAddKeysToAgent yes\nHashKnownHosts yes\n")

    ctx = SystemContext(root=tmp_path)
    mod = scan_ssh(ctx)

    assert isinstance(mod, Ssh)
    assert mod.forwardX11 is True
    assert mod.startAgent is True
    assert "HashKnownHosts yes" in mod.extraConfig
    assert mod.resolve_claims() == {"openssh"}

    fragment = mod.to_nix_fragment(name="ssh")
    assert fragment.name == "ssh"
    assert fragment["programs.ssh"].value == {
        "forwardX11": True,
        "startAgent": True,
        "extraConfig": "HashKnownHosts yes",
    }


def test_ssh_client_enabled_with_config_dir(tmp_path):
    conf_dir = tmp_path / "etc" / "ssh" / "ssh_config.d"
    conf_dir.mkdir(parents=True)
    (conf_dir / "10-agent.conf").write_text("AddKeysToAgent yes\n")

    ctx = SystemContext(root=tmp_path)
    mod = scan_ssh(ctx)

    assert isinstance(mod, Ssh)
    assert mod.startAgent is True
    assert mod.resolve_claims() == {"openssh"}

    fragment = mod.to_nix_fragment(name="ssh")
    assert fragment["programs.ssh"].value == {
        "startAgent": True,
    }


def test_ssh_client_enabled_via_binary(tmp_path):
    bin_dir = tmp_path / "usr" / "bin"
    bin_dir.mkdir(parents=True)
    ssh_bin = bin_dir / "ssh"
    ssh_bin.touch(mode=0o755)

    ctx = SystemContext(root=tmp_path)
    mod = scan_ssh(ctx)

    assert isinstance(mod, Ssh)
    assert mod.resolve_claims() == {"openssh"}
