from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class GroupsScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {}

        if not context.path_exists("/etc/group"):
            return {}

        content = context.read_file("/etc/group")

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(":")
            if len(parts) < 3:
                continue

            group_name = parts[0]
            try:
                gid = int(parts[2])
            except ValueError:
                continue

            members_str = parts[3] if len(parts) > 3 else ""
            members = [m.strip() for m in members_str.split(",") if m.strip()]

            # skip system groups
            if gid < 1000 or gid == 65534 or group_name in ["nogroup", "nobody"]:
                continue

            # skip nixbld group
            if group_name == "nixbld":
                continue

            ir[group_name] = {
                "gid": gid,
                "members": members,
            }

        return {"groups": ir}


class GroupsMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        groups_data = ir.get("groups")
        if not groups_data:
            return None

        nix_groups = {}

        for name, info in groups_data.items():
            group_conf = {
                "gid": info["gid"],
            }

            if info["members"]:
                group_conf["members"] = info["members"]

            nix_groups[name] = group_conf

        return SimpleOptionBlock(
            name="groups",
            description="Existing user groups",
            data={"users.groups": nix_groups},
        )


module = Module("groups", GroupsScanner(), GroupsMapper())
