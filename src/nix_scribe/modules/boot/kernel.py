import logging
from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

logger = logging.getLogger(__name__)

kernel = Module("boot.kernel")

ETC_MODULES_PATH = "/etc/modules"
ETC_MODULES_LOAD_D_PATH = "/etc/modules-load.d"
ETC_MODPROBE_D_PATH = "/etc/modprobe.d"
ETC_CMDLINE_PATHS = [
    "/etc/cmdline",
    "/etc/kernel/cmdline",
]


def _parse_modules_file(content: str) -> list[str]:
    modules = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        parts = line.split()
        if parts:
            modules.append(parts[0])
    return modules


@kernel.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ir: dict[str, Any] = {}

    # 1. Scan auto-loaded modules (/etc/modules, /etc/modules-load.d/*.conf)
    kernel_modules: list[str] = []

    if context.path_exists(ETC_MODULES_PATH):
        content = context.read_file(ETC_MODULES_PATH)
        kernel_modules.extend(_parse_modules_file(content))

    if context.path_exists(ETC_MODULES_LOAD_D_PATH):
        for filename in context.list_directory(ETC_MODULES_LOAD_D_PATH):
            if filename.endswith(".conf"):
                filepath = f"{ETC_MODULES_LOAD_D_PATH}/{filename}"
                content = context.read_file(filepath)
                kernel_modules.extend(_parse_modules_file(content))

    if kernel_modules:
        ir["kernelModules"] = sorted(list(dict.fromkeys(kernel_modules)))

    # 2. Scan modprobe configuration (/etc/modprobe.d/*.conf)
    blacklisted: list[str] = []
    extra_modprobe: list[str] = []

    if context.path_exists(ETC_MODPROBE_D_PATH):
        for filename in context.list_directory(ETC_MODPROBE_D_PATH):
            if filename.endswith(".conf"):
                filepath = f"{ETC_MODPROBE_D_PATH}/{filename}"
                content = context.read_file(filepath)
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
                        extra_modprobe.append(stripped)

    if blacklisted:
        ir["blacklistedKernelModules"] = sorted(list(dict.fromkeys(blacklisted)))

    if extra_modprobe:
        ir["extraModprobeConfig"] = "\n".join(extra_modprobe)

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
