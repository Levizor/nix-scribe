from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.users.groups import GroupEntry, Groups

groups = Scanner(
    "users.groups",
    description="Existing user groups",
)


@groups.scanner()
def scan(context: SystemContext) -> Groups | None:
    if not context.path_exists("/etc/group"):
        return None

    content = context.read_file("/etc/group")
    mod = Groups()

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

        if gid < 1000 or gid == 65534 or group_name in ["nogroup", "nobody"]:
            continue

        if group_name == "nixbld":
            continue

        mod.groups[group_name] = GroupEntry(gid=gid, members=members)

    if not mod.groups:
        return None

    return mod
