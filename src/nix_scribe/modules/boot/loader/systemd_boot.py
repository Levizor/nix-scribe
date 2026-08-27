import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.kv import is_truthy, parse_space_kv
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

systemd_boot = Module("boot.loader.systemd-boot")

LOADER_CONF_BOOT = "/boot/loader/loader.conf"
LOADER_CONF_EFI = "/efi/loader/loader.conf"
SYSTEMD_BOOT_EFI_PATHS = [
    "/boot/EFI/systemd/systemd-bootx64.efi",
    "/boot/EFI/BOOT/BOOTX64.EFI",
    "/efi/EFI/systemd/systemd-bootx64.efi",
]


@systemd_boot.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    has_conf_boot = context.path_exists(LOADER_CONF_BOOT)
    has_conf_efi = context.path_exists(LOADER_CONF_EFI)
    has_entries = context.path_exists("/boot/loader/entries") or context.path_exists(
        "/efi/loader/entries"
    )
    has_efi_binary = any(context.path_exists(p) for p in SYSTEMD_BOOT_EFI_PATHS)

    if not (has_conf_boot or has_conf_efi or has_entries or has_efi_binary):
        return {}

    ir: dict[str, Any] = {"enable": True}

    conf_path = (
        LOADER_CONF_BOOT
        if has_conf_boot
        else (LOADER_CONF_EFI if has_conf_efi else None)
    )

    if conf_path:
        reader = ConfigReader(context, parse_space_kv)
        config = reader.read_config(conf_path)

        if "console-mode" in config:
            ir["consoleMode"] = config["console-mode"]

        if "editor" in config:
            ir["editor"] = is_truthy(config["editor"])

        if "sort-key" in config:
            ir["sortKey"] = config["sort-key"]

        if "xbootldr-mount-point" in config:
            ir["xbootldrMountPoint"] = config["xbootldr-mount-point"]

    return ir


@systemd_boot.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir or not ir.get("enable"):
        return None

    boot_config: dict[str, Any] = {"enable": True}

    if "consoleMode" in ir:
        boot_config["consoleMode"] = ir["consoleMode"]

    if "editor" in ir:
        boot_config["editor"] = ir["editor"]

    if "sortKey" in ir:
        boot_config["sortKey"] = ir["sortKey"]

    if "xbootldrMountPoint" in ir:
        boot_config["xbootldrMountPoint"] = ir["xbootldrMountPoint"]

    return ConfigFragment(
        name="systemd-boot",
        description="systemd-boot UEFI Bootloader Configuration",
        data={"boot.loader.systemd-boot": boot_config},
    )
