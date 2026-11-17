from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.users.groups import Groups
from nix_scribe.scanners.users.groups import groups

MOCK_GROUP = """root:x:0:
users:x:100:
wheel:x:10:alice,bob
mygroup:x:1000:alice
othergroup:x:1001:
nixbld:x:30000:
"""


def test_groups_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert groups.scan(context) is None


def test_groups_scanner(tmp_path):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/group").write_text(MOCK_GROUP)

    context = SystemContext(tmp_path)
    mod = groups.scan(context)

    assert isinstance(mod, Groups)
    assert "mygroup" in mod.groups
    assert "othergroup" in mod.groups
    assert "wheel" not in mod.groups
    assert "nixbld" not in mod.groups

    assert mod.groups["mygroup"].gid == 1000
    assert mod.groups["mygroup"].members == ["alice"]

    fragment = mod.to_nix_fragment()
    data = fragment["users.groups"].value
    assert data["mygroup"]["gid"] == 1000
    assert data["mygroup"]["members"] == ["alice"]
    assert "members" not in data["othergroup"]
