import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

kernel = Module("boot.kernel")

MODULES_PATHS = [
    "/etc/modules",
    "/etc/modules-load.d",
]

MODPROBE_PATHS = [
    "/etc/modprobe.d",
]

ETC_CMDLINE_PATHS = [
    "/etc/cmdline",
    "/etc/kernel/cmdline",
]


def _parse_modules(content: str) -> dict[str, Any]:
    modules = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ";")):
            parts = line.split()
            if parts:
                modules.append(parts[0])
    return {"modules": modules}


def _parse_modprobe(content: str) -> dict[str, Any]:
    blacklisted = []
    extra = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[0] == "blacklist":
            blacklisted.append(parts[1])
        elif (
            len(parts) >= 3
            and parts[0] == "install"
            and parts[2] in ("/bin/true", "/bin/false", "/bin/disabled")
        ):
            blacklisted.append(parts[1])
        else:
            extra.append(stripped)

    return {"blacklisted": blacklisted, "extra": extra}


@kernel.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ir: dict[str, Any] = {}

    # 1. Scan auto-loaded modules (/etc/modules, /etc/modules-load.d)
    modules_reader = ConfigReader(context, _parse_modules)
    modules_config = modules_reader.read_merge_configs_from_paths_list(MODULES_PATHS)
    if modules_config.get("modules"):
        ir["kernelModules"] = sorted(list(dict.fromkeys(modules_config["modules"])))

    # 2. Scan modprobe configuration (/etc/modprobe.d)
    modprobe_reader = ConfigReader(context, _parse_modprobe)
    modprobe_config = modprobe_reader.read_merge_configs_from_paths_list(MODPROBE_PATHS)
    if modprobe_config.get("blacklisted"):
        ir["blacklistedKernelModules"] = sorted(
            list(dict.fromkeys(modprobe_config["blacklisted"]))
        )
    if modprobe_config.get("extra"):
        ir["extraModprobeConfig"] = "\n".join(modprobe_config["extra"])

    # 3. Scan kernel command line (/etc/cmdline or /etc/kernel/cmdline)
    cmdline_path = next((p for p in ETC_CMDLINE_PATHS if context.path_exists(p)), None)
    if cmdline_path:
        content = context.read_file(cmdline_path).strip()
        if content:
            ir["kernelParams"] = content.split()

    return ir


@kernel.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir:
        return None

    boot_config: dict[str, Any] = {}

    if "kernelModules" in ir:
        boot_config["kernelModules"] = ir["kernelModules"]

    if "blacklistedKernelModules" in ir:
        boot_config["blacklistedKernelModules"] = ir["blacklistedKernelModules"]

    if "kernelParams" in ir:
        boot_config["kernelParams"] = ir["kernelParams"]

    if "extraModprobeConfig" in ir:
        boot_config["extraModprobeConfig"] = ir["extraModprobeConfig"]

    if not boot_config:
        return None

    return ConfigFragment(
        name="kernel",
        description="Kernel Modules and Parameters Configuration",
        data={"boot": boot_config},
    )
