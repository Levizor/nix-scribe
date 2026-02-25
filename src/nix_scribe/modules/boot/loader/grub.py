import logging
from pathlib import Path
from typing import Any

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import BaseOptionBlock, SimpleOptionBlock
from nix_scribe.lib.parsers.kv import parse_kv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module

logger = logging.getLogger(__name__)

GRUB_DEFAULT_PATH = "/etc/default/grub"
GRUB_CONFIG_PATH = "/boot/grub/grub.cfg"


class GrubScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {
            "enable": False,
            "efiSupport": False,
            "useOSProber": False,
            "enableCryptodisk": False,
            "timeout": 5,
            "zfsSupport": False,
            "default": "0",
        }

        has_config = context.path_exists(GRUB_CONFIG_PATH)
        has_default = context.path_exists(GRUB_DEFAULT_PATH)
        has_bin = bool(
            context.find_executable_path("grub-install")
            or context.find_executable_path("grub-mkconfig")
        )

        if not (has_config or has_default or has_bin):
            return {}

        ir["enable"] = True

        if context.path_exists("/sys/firmware/efi"):
            ir["efiSupport"] = True

        try:
            mount_output = context.run_command(["mount"])
            if "type zfs" in mount_output:
                ir["zfsSupport"] = True
        except Exception:
            pass

        if has_default:
            try:
                reader = ConfigReader(context, parse_kv)
                config = reader.read_config(GRUB_DEFAULT_PATH)
                self._analyze_config(config, ir, context)
            except Exception as e:
                logger.warning(f"Failed to parse GRUB config: {e}")

        return ir

    def _analyze_config(
        self, config: dict[str, Any], ir: dict[str, Any], context: SystemContext
    ) -> None:
        if "GRUB_TIMEOUT" in config:
            try:
                ir["timeout"] = int(config["GRUB_TIMEOUT"])
            except ValueError:
                logger.warning("Failed to parse timeout value in grub config")

        if "GRUB_TIMEOUT_STYLE" in config:
            ir["timeoutStyle"] = config["GRUB_TIMEOUT_STYLE"]

        if "GRUB_DEFAULT" in config:
            ir["default"] = config["GRUB_DEFAULT"]

        if "GRUB_DISABLE_OS_PROBER" in config:
            ir["useOSProber"] = str(config["GRUB_DISABLE_OS_PROBER"]).lower() == "false"

        if "GRUB_ENABLE_CRYPTODISK" in config:
            val = str(config["GRUB_ENABLE_CRYPTODISK"]).lower()
            ir["enableCryptodisk"] = val in ("y", "yes", "true")

        if "GRUB_BACKGROUND" in config:
            if context.path_exists(config["GRUB_BACKGROUND"]):
                ir["splashImage"] = config["GRUB_BACKGROUND"]


class GrubMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> BaseOptionBlock | None:
        if not ir or not ir.get("enable", False):
            return None

        grub_config: dict[str, Any] = {
            "enable": True,
        }

        if ir.get("efiSupport"):
            grub_config["efiSupport"] = True

        if ir.get("zfsSupport"):
            grub_config["zfsSupport"] = True

        if ir.get("default") and ir["default"] != "0":
            grub_config["default"] = ir["default"]

        if "timeoutStyle" in ir:
            grub_config["timeoutStyle"] = ir["timeoutStyle"]

        if ir.get("useOSProber"):
            grub_config["useOSProber"] = True

        if ir.get("enableCryptodisk"):
            grub_config["enableCryptodisk"] = True

        if "splashImage" in ir:
            source_path = ir["splashImage"]
            target_filename = f"boot-loader-grub-{Path(source_path).name}"
            grub_config["splashImage"] = Asset(source_path, target_filename)

        return SimpleOptionBlock(
            name="boot/loader/grub",
            description="GRUB Bootloader Configuration",
            data={"boot.loader.grub": grub_config},
        )


module = Module("grub", GrubScanner(), GrubMapper())
