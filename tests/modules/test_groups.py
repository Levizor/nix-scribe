from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.users.groups import groups

MOCK_GROUP = """root:x:0:
users:x:100:
wheel:x:10:alice,bob
mygroup:x:1000:alice
othergroup:x:1001:
nixbld:x:30000:
"""


def test_groups_scanner(tmp_path):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/group").write_text(MOCK_GROUP)

    context = SystemContext(tmp_path)
    ir = groups.scan(context)

    assert "groups" in ir
    assert "mygroup" in ir["groups"]
    assert "othergroup" in ir["groups"]
    assert "wheel" not in ir["groups"]  # system group < 1000
    assert "nixbld" not in ir["groups"]

    assert ir["groups"]["mygroup"]["gid"] == 1000
    assert ir["groups"]["mygroup"]["members"] == ["alice"]


def test_groups_mapper():
    mock_ir = {
        "groups": {
            "mygroup": {"gid": 1000, "members": ["alice"]},
            "othergroup": {"gid": 1001, "members": []},
        }
    }

    block = groups.map(mock_ir)
    assert block is not None

    assert block["users.groups"]["mygroup"]["gid"] == 1000
    assert block["users.groups"]["mygroup"]["members"] == ["alice"]
    assert "members" not in block["users.groups"]["othergroup"]
