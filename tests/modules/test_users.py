from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.users.users import users_module

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


def test_users_scanner(tmp_path):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/passwd").write_text(MOCK_PASSWD)
    (tmp_path / "etc/group").write_text(MOCK_GROUP)
    (tmp_path / "etc/shadow").write_text(MOCK_SHADOW)

    context = SystemContext(tmp_path)
    ir = users_module.scan(context)

    assert "users" in ir
    assert "alice" in ir["users"]
    assert "bob" in ir["users"]
    assert "root" not in ir["users"]
    assert "nixbld1" not in ir["users"]

    alice = ir["users"]["alice"]
    assert alice["uid"] == 1000
    assert alice["group"] == "alice"
    assert "wheel" in alice["extraGroups"]
    assert alice["hashedPassword"] == "$6$hash"

    bob = ir["users"]["bob"]
    assert bob["shell"] == "/usr/bin/zsh"
    assert bob["hashedPassword"] is None


def test_users_mapper():
    mock_ir = {
        "users": {
            "alice": {
                "uid": 1000,
                "description": "Alice",
                "home": "/home/alice",
                "group": "alice",
                "extraGroups": ["wheel", "video"],
                "shell": "/bin/bash",
                "hashedPassword": "$6$hash",
            }
        }
    }

    block = users_module.map(mock_ir)
    assert block is not None

    alice_conf = block["users.users"]["alice"]
    assert alice_conf["isNormalUser"]
    assert alice_conf["uid"] == 1000
    assert alice_conf["extraGroups"] == ["wheel", "video"]
    assert block["programs.bash.enable"]
