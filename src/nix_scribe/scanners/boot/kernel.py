import logging

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.parsers.kernel import parse_modprobe, parse_modules
from nix_scribe.lib.parsers.parser import ConfigReader
from nix_scribe.lib.registry import Scanner
from nix_scribe.modules.nixos.boot.kernel import Kernel

logger = logging.getLogger(__name__)

kernel = Scanner("boot.kernel")

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


@kernel.scanner()
def scan(context: SystemContext) -> Kernel | None:
    mod = Kernel()

    modules_reader = ConfigReader(context, parse_modules)
    modules_config = modules_reader.read_merge_configs_from_paths_list(MODULES_PATHS)
    if modules_config.get("modules"):
        mod.kernelModules = sorted(list(dict.fromkeys(modules_config["modules"])))

    modprobe_reader = ConfigReader(context, parse_modprobe)
    modprobe_config = modprobe_reader.read_merge_configs_from_paths_list(MODPROBE_PATHS)
    if modprobe_config.get("blacklisted"):
        mod.blacklistedKernelModules = sorted(
            list(dict.fromkeys(modprobe_config["blacklisted"]))
        )
    if modprobe_config.get("extra"):
        mod.extraModprobeConfig = "\n".join(modprobe_config["extra"])

    cmdline_path = next((p for p in ETC_CMDLINE_PATHS if context.path_exists(p)), None)
    if cmdline_path:
        content = context.read_file(cmdline_path).strip()
        if content:
            mod.kernelParams = content.split()

    return mod
