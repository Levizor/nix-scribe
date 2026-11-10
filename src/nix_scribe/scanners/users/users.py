from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.users.users import (
    SubGidRange,
    SubUidRange,
    UserEntry,
    Users,
)

users_module = Scanner("users.users")


def _parse_passwd_normal_users(text: str) -> dict[str, dict[str, Any]]:
    """Parses /etc/passwd and filters for normal users."""
    users: dict[str, dict[str, Any]] = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 7:
            continue

        username, _, uid_str, gid_str, gecos, home, shell = parts[:7]
        uid, gid = int(uid_str), int(gid_str)

        if uid < 1000 or uid == 65534 or username == "nobody":
            continue

        if "nixbld" in username:
            continue

        users[username] = {
            "uid": uid,
            "gid": gid,
            "description": gecos.split(",")[0],
            "home": home,
            "shell": shell,
            "hashedPassword": None,
            "expires": None,
            "subUidRanges": [],
            "subGidRanges": [],
        }
    return users


def _add_shadow_hashes_and_expirations(text: str, users_ir: dict[str, dict[str, Any]]):
    """Parses /etc/shadow for password hashes and account expiration."""
    for line in text.splitlines():
        parts = line.split(":")
        if len(parts) < 2:
            continue
        name, pwd = parts[0], parts[1]

        if name in users_ir:
            if pwd not in ["!", "*", "!!", ""]:
                users_ir[name]["hashedPassword"] = pwd

            if len(parts) > 7 and parts[7]:
                users_ir[name]["expires"] = parts[7]


def _parse_groups(text: str) -> tuple[dict[int, str], dict[str, list[str]]]:
    """Parses /etc/group into primary GID map and secondary group map."""
    gid_map: dict[int, str] = {}
    secondary_map: dict[str, list[str]] = {}

    for line in text.splitlines():
        parts = line.split(":")
        if len(parts) < 4:
            continue

        group_name = parts[0]
        gid = int(parts[2])
        members = parts[3].split(",") if parts[3] else []

        gid_map[gid] = group_name

        for user in members:
            if user:
                if user not in secondary_map:
                    secondary_map[user] = []
                secondary_map[user].append(group_name)

    return gid_map, secondary_map


def _add_sub_ids(text: str, users_ir: dict[str, dict[str, Any]], key: str):
    """Parses subordinate ID files (subuid/subgid)."""
    for line in text.splitlines():
        parts = line.split(":")
        if len(parts) == 3 and parts[0] in users_ir:
            users_ir[parts[0]][key].append(
                {"start": int(parts[1]), "count": int(parts[2])}
            )


@users_module.scanner()
def scan(context: SystemContext) -> Users | None:
    if not context.path_exists("/etc/passwd"):
        return None

    users_ir = _parse_passwd_normal_users(context.read_file("/etc/passwd"))
    if not users_ir:
        return None

    try:
        _add_shadow_hashes_and_expirations(context.read_file("/etc/shadow"), users_ir)
    except Exception:
        pass

    gid_map: dict[int, str] = {}
    secondary_map: dict[str, list[str]] = {}
    if context.path_exists("/etc/group"):
        gid_map, secondary_map = _parse_groups(context.read_file("/etc/group"))

    for file_path, key in [
        ("/etc/subuid", "subUidRanges"),
        ("/etc/subgid", "subGidRanges"),
    ]:
        if context.path_exists(file_path):
            _add_sub_ids(context.read_file(file_path), users_ir, key)

    mod = Users()

    for username, info in users_ir.items():
        primary_group = gid_map.get(info["gid"], "users")
        extras = list(secondary_map.get(username, []))
        if primary_group in extras:
            extras.remove(primary_group)

        shell_val = None
        shell_path = info.get("shell", "")
        if "bash" in shell_path:
            shell_val = raw("pkgs.bash")
            mod.bash_enable = True
        elif "zsh" in shell_path:
            shell_val = raw("pkgs.zsh")
            mod.zsh_enable = True
        elif "fish" in shell_path:
            shell_val = raw("pkgs.fish")
            mod.fish_enable = True

        auth_keys: list[str] = []
        ssh_keys_path = f"{info['home']}/.ssh/authorized_keys"
        if context.path_exists(ssh_keys_path):
            try:
                keys = context.read_file(ssh_keys_path).splitlines()
                auth_keys = [
                    k.strip() for k in keys if k.strip() and not k.startswith("#")
                ]
            except Exception:
                pass

        mod.users[username] = UserEntry(
            isNormalUser=True,
            uid=info["uid"],
            description=info["description"],
            home=info["home"],
            group=primary_group,
            extraGroups=extras,
            hashedPassword=info.get("hashedPassword"),
            expires=info.get("expires"),
            shell=shell_val,
            authorized_keys=auth_keys,
            subUidRanges=[
                SubUidRange(startUid=r["start"], count=r["count"])
                for r in info["subUidRanges"]
            ],
            subGidRanges=[
                SubGidRange(startGid=r["start"], count=r["count"])
                for r in info["subGidRanges"]
            ],
        )

    return mod
