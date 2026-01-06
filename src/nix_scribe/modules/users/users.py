from typing import Any, Dict, List, Tuple

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class UsersScanner(BaseScanner):
    def _parse_passwd_normal_users(self, text: str) -> dict[str, Any]:
        """Parses /etc/passwd and filters for normal users."""
        users = {}
        for line in text.splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 7:
                continue

            username, _, uid_str, gid_str, gecos, home, shell = parts[:7]
            uid, gid = int(uid_str), int(gid_str)

            # skip system users
            if uid < 1000 or username == "nobody":
                continue

            users[username] = {
                "uid": uid,
                "gid": gid,
                "description": gecos.split(",")[0],
                "home": home,
                "shell": shell,
                "hashedPassword": None,
                "openssh": {"authorizedKeys": {"keys": []}},
                "subUidRanges": [],
                "subGidRanges": [],
                "extraGroups": [],
            }
        return users

    def _add_shadow_hashes_and_expirations(self, text: str, users_ir: dict[str, Any]):
        """Parses /etc/shadow for password hashes and account expiration."""
        for line in text.splitlines():
            parts = line.split(":")
            if len(parts) < 2:
                continue
            name, pwd = parts[0], parts[1]

            if name in users_ir:
                # password hash
                if pwd not in ["!", "*", "!!", ""]:
                    users_ir[name]["hashedPassword"] = pwd

                # account expiration
                if len(parts) > 7 and parts[7]:
                    users_ir[name]["expires"] = parts[7]

    def _parse_groups(self, text: str) -> Tuple[dict[int, str], dict[str, List[str]]]:
        """
        Parses /etc/group.
        Returns:
            1. A map of GID -> Group Name (for primary groups).
            2. A map of Username -> List of Group Names (for secondary groups).
        """
        gid_map = {}
        secondary_map: Dict[str, List[str]] = {}

        for line in text.splitlines():
            parts = line.split(":")
            if len(parts) < 4:
                continue

            group_name = parts[0]
            gid = int(parts[2])
            members = parts[3].split(",") if parts[3] else []

            gid_map[gid] = group_name

            # track each member secondary group
            for user in members:
                if user:
                    if user not in secondary_map:
                        secondary_map[user] = []
                    secondary_map[user].append(group_name)

        return gid_map, secondary_map

    def _add_sub_ids(self, text: str, users_ir: dict[str, Any], key: str):
        """Parses subordinate ID files (subuid/subgid)."""
        for line in text.splitlines():
            parts = line.split(":")
            if len(parts) == 3 and parts[0] in users_ir:
                users_ir[parts[0]][key].append(
                    {"start": int(parts[1]), "count": int(parts[2])}
                )

    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = self._parse_passwd_normal_users(context.read_file("/etc/passwd"))

        # hashes, expirations
        try:
            self._add_shadow_hashes_and_expirations(
                context.read_file("/etc/shadow"), ir
            )
        except Exception:
            pass

        # primary and secondary groups
        gid_map, secondary_map = self._parse_groups(context.read_file("/etc/group"))

        for username, user_data in ir.items():
            primary_group = gid_map.get(user_data["gid"], "users")
            user_data["group"] = primary_group

            extras = secondary_map.get(username, [])
            if primary_group in extras:
                extras.remove(primary_group)
            user_data["extraGroups"] = extras

        # sub U/G id ranges
        for file_path, key in [
            ("/etc/subuid", "subUidRanges"),
            ("/etc/subgid", "subGidRanges"),
        ]:
            if context.path_exists(file_path):
                self._add_sub_ids(context.read_file(file_path), ir, key)

        # ssh authorized keys
        for data in ir.values():
            ssh_keys_path = f"{data['home']}/.ssh/authorized_keys"
            if context.path_exists(ssh_keys_path):
                try:
                    keys = context.read_file(ssh_keys_path).splitlines()
                    data["openssh"]["authorizedKeys"]["keys"] = [
                        k.strip() for k in keys if k.strip() and not k.startswith("#")
                    ]
                except Exception:
                    pass

        return {"users": ir}


class UsersMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        users_data = ir.get("users")
        if not users_data:
            return None

        users = {}
        required_args = set()
        enabled_shells = {}

        for name, info in users_data.items():
            user_conf = {
                "isNormalUser": True,
                "uid": info["uid"],
                "description": info["description"],
                "home": info["home"],
                "group": info["group"],
            }

            if info.get("extraGroups"):
                user_conf["extraGroups"] = info["extraGroups"]

            if info.get("hashedPassword"):
                user_conf["hashedPassword"] = info["hashedPassword"]

            if info.get("expires"):
                user_conf["expires"] = info["expires"]

            shell_path = info.get("shell", "")
            if "bash" in shell_path:
                user_conf["shell"] = raw("pkgs.bash")
                enabled_shells["programs.bash.enable"] = True
                required_args.add("pkgs")
            elif "zsh" in shell_path:
                user_conf["shell"] = raw("pkgs.zsh")
                enabled_shells["programs.zsh.enable"] = True
                required_args.add("pkgs")
            elif "fish" in shell_path:
                user_conf["shell"] = raw("pkgs.fish")
                enabled_shells["programs.fish.enable"] = True
                required_args.add("pkgs")

            ssh_keys = info.get("openssh", {}).get("authorizedKeys", {}).get("keys", [])
            if ssh_keys:
                user_conf["openssh.authorizedKeys.keys"] = ssh_keys

            if info.get("subUidRanges"):
                user_conf["subUidRanges"] = [
                    {"startUid": r["start"], "count": r["count"]}
                    for r in info["subUidRanges"]
                ]
            if info.get("subGidRanges"):
                user_conf["subGidRanges"] = [
                    {"startGid": r["start"], "count": r["count"]}
                    for r in info["subGidRanges"]
                ]

            users[name] = user_conf

        return SimpleOptionBlock(
            name="users",
            description="User accounts and subordinate ID ranges",
            data={"users.users": users, **enabled_shells},
            arguments=list(required_args),
        )


module = Module("users", UsersScanner(), UsersMapper())
