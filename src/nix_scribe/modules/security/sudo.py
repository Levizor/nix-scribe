import json
import logging
import shutil
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import BaseOptionBlock, SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)

SUDOERS_PATH = "/etc/sudoers"


class SudoScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        cvtsudoers_path = shutil.which("cvtsudoers")
        sudo_path = context.find_executable_path("sudo")

        if (
            not cvtsudoers_path
            or not sudo_path
            or not context.path_exists(SUDOERS_PATH)
        ):
            logger.debug(f"cvtsudoers_path: {cvtsudoers_path}")
            logger.debug(f"sudo_path: {sudo_path}")
            logger.warning("No sudo configuration or cvtsudoers not found")
            return {}

        ir = {
            "enable": True,
            "wheelNeedsPassword": True,
            "execWheelOnly": False,
            "keepTerminfo": False,
            "extraConfigLines": [],
        }

        # Get Effective Config as TEXT (for extraConfig)
        text_output = context.run_command(
            [cvtsudoers_path, "-b", "/etc", "-e", "-f", "sudoers", SUDOERS_PATH],
        )
        ir["extraConfigLines"] = [
            line for line in text_output.splitlines() if line.strip()
        ]

        # Get Effective Config as JSON (for Analysis)
        json_output = context.run_command(
            [cvtsudoers_path, "-f", "json", "-e", SUDOERS_PATH]
        )
        json_data = json.loads(json_output)
        self._analyze_json(json_data, ir)

        # Check Permissions for execWheelOnly
        stat_output = context.run_command(["stat", "-c", "%a %G", sudo_path]).strip()

        if stat_output:
            mode_octal, group = stat_output.split()
            others_perm = int(mode_octal[-1])
            is_world_exec = (others_perm & 1) == 1
            if not is_world_exec:
                ir["execWheelOnly"] = True

        return ir

    def _analyze_json(self, data: dict, ir: dict):
        """
        Analyzes the structured JSON to find high-level patterns.
        """
        # Analyze Defaults for keepTerminfo
        defaults = data.get("Defaults", [])
        for entry in defaults:
            for opt in entry.get("Options", []):
                # Check for env_keep lists containing TERMINFO
                if "env_keep" in opt:
                    values = opt["env_keep"]
                    if "TERMINFO" in values or "TERMINFO_DIRS" in values:
                        ir["keepTerminfo"] = True

        # Analyze Privileges for wheel NOPASSWD
        specs = data.get("User_Specs", data.get("Privileges", []))
        for spec in specs:
            users = self._get_users(spec.get("User_List", []))

            if "%wheel" in users:
                for cmnd_spec in spec.get("Cmnd_Specs", []):
                    opts = cmnd_spec.get("Options", [])
                    for opt in opts:
                        if opt.get("authenticate") is False:
                            ir["wheelNeedsPassword"] = False

    def _get_users(self, member_list: list[dict[str, Any]]) -> list[str]:
        users = []
        for m in member_list:
            if "usergroup" in m:
                users.append(f"%{m['usergroup']}")
            if "username" in m:
                users.append(m["username"])
        return users


class SudoMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> BaseOptionBlock | None:
        if not ir or not ir.get("enable", False):
            return None

        sudo_config = {"enable": True}

        if ir.get("execWheelOnly"):
            sudo_config["execWheelOnly"] = True

        if ir.get("wheelNeedsPassword") is False:
            sudo_config["wheelNeedsPassword"] = False

        raw_lines = ir.get("extraConfigLines", [])
        filtered_lines = []

        for line in raw_lines:
            # Filter out Wheel NOPASSWD rules if mapped
            if (
                sudo_config.get("wheelNeedsPassword") is False
                and "%wheel" in line
                and "NOPASSWD" in line
            ):
                continue

            # Filter out TERMINFO defaults if mapped
            if ir.get("keepTerminfo") and "env_keep" in line and "TERMINFO" in line:
                continue

            # Filter out standard root rule
            if line.startswith("root ") and "ALL" in line and "(ALL" in line:
                continue

            filtered_lines.append(line)

        # if filtered_lines:
        #     sudo_config["extraConfig"] = "\n".join(filtered_lines)

        return SimpleOptionBlock(
            name="security/sudo",
            description="Sudo Configuration",
            data={"security.sudo": sudo_config},
        )


module = Module("sudo", SudoScanner(), SudoMapper())
