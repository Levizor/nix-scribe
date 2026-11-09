from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.users.users import Users
from nix_scribe.scanners.users.users import users_module

MOCK_PASSWD = """root:x:0:0:root:/root:/bin/bash
alice:x:1000:1000:Alice,,,:/home/alice:/bin/bash
bob:x:1001:1001:Bob,,,:/home/bob:/usr/bin/zsh
nixbld1:x:30001:30000:Nix build user 1,,,:/var/empty:/run/current-system/sw/bin/nologin
"""

MOCK_GROUP = """root:x:0:
alice:x:1000:
bob:x:1001:
users:x:100:
wheel:x:10:alice,bob
"""

MOCK_SHADOW = """root:*:19000:0:99999:7:::
alice:$6$hash:19000:0:99999:7:::
bob:!:19000:0:99999:7:::
"""


def test_users_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert users_module.scan(context) is None


def test_users_scanner(tmp_path):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/passwd").write_text(MOCK_PASSWD)
    (tmp_path / "etc/group").write_text(MOCK_GROUP)
    (tmp_path / "etc/shadow").write_text(MOCK_SHADOW)

    context = SystemContext(tmp_path)
    mod = users_module.scan(context)

    assert isinstance(mod, Users)
    assert "alice" in mod.users
    assert "bob" in mod.users
    assert "root" not in mod.users
    assert "nixbld1" not in mod.users

    alice = mod.users["alice"]
    assert alice.isNormalUser is True
    assert alice.uid == 1000
    assert alice.group == "alice"
    assert "wheel" in alice.extraGroups
    assert alice.hashedPassword == "$6$hash"

    bob = mod.users["bob"]
    assert str(bob.shell) == "pkgs.zsh"
    assert bob.hashedPassword is None

    assert mod.bash_enable is True
    assert mod.zsh_enable is True

    fragment = mod.to_nix_fragment()
    assert "pkgs" in fragment.arguments
    assert fragment["programs.bash.enable"].value is True
    assert fragment["programs.zsh.enable"].value is True
    alice_conf = fragment["users.users"].value["alice"]
    assert alice_conf["isNormalUser"] is True
    assert alice_conf["uid"] == 1000
    assert alice_conf["extraGroups"] == ["wheel"]
