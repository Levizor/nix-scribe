import logging
from pathlib import Path
from typing import Any

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.kv import parse_kv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.boot.loader.grub import Grub

logger = logging.getLogger(__name__)

grub = Scanner(
    "boot.loader.grub",
    description="GRUB Bootloader Configuration",
)

GRUB_DEFAULT_PATH = "/etc/default/grub"
GRUB_CONFIG_PATH = "/boot/grub/grub.cfg"


def _analyze_config(config: dict[str, Any], mod: Grub, context: SystemContext) -> None:
    if "GRUB_TIMEOUT_STYLE" in config:
        mod.timeoutStyle = config["GRUB_TIMEOUT_STYLE"]

    if "GRUB_DEFAULT" in config:
        mod.default = config["GRUB_DEFAULT"]

    if "GRUB_DISABLE_OS_PROBER" in config:
        mod.useOSProber = str(config["GRUB_DISABLE_OS_PROBER"]).lower() == "false"

    if "GRUB_ENABLE_CRYPTODISK" in config:
        val = str(config["GRUB_ENABLE_CRYPTODISK"]).lower()
        mod.enableCryptodisk = val in ("y", "yes", "true")

    if "GRUB_BACKGROUND" in config:
        bg_path = config["GRUB_BACKGROUND"]
        if context.path_exists(bg_path):
            try:
                content = context.read_file_bytes(bg_path)
                target_filename = f"boot-loader-grub-{Path(bg_path).name}"
                mod.splashImage = Asset(target_filename, content)
            except Exception as e:
                logger.warning(f"Failed to read GRUB splash image: {e}")


@grub.scanner()
def scan(context: SystemContext) -> Grub | None:
    has_config = context.path_exists(GRUB_CONFIG_PATH)
    has_default = context.path_exists(GRUB_DEFAULT_PATH)
    has_bin = bool(
        context.find_executable_path("grub-install")
        or context.find_executable_path("grub-mkconfig")
    )

    if not (has_config or has_default or has_bin):
        return None

    mod = Grub(enable=True)

    if context.path_exists("/sys/firmware/efi"):
        mod.efiSupport = True

    if context.path_exists("/etc/fstab"):
        try:
            if "zfs" in context.read_file("/etc/fstab"):
                mod.zfsSupport = True
        except Exception:
            pass

    if not mod.zfsSupport and context.path_exists("/proc/mounts"):
        try:
            if "zfs" in context.read_file("/proc/mounts"):
                mod.zfsSupport = True
        except Exception:
            pass

    if has_default:
        try:
            reader = ConfigReader(context, parse_kv)
            config = reader.read_config(GRUB_DEFAULT_PATH)
            _analyze_config(config, mod, context)
        except Exception as e:
            logger.warning(f"Failed to parse GRUB config: {e}")

    return mod
