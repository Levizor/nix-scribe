from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

nano = Module("programs.nano")


@nano.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    ir = {}
    enabled = bool(context.find_executable_path("nano"))

    if not enabled:
        return ir

    ir["enable"] = True

    if context.path_exists("/etc/nanorc"):
        ir["nanorc"] = context.read_file("/etc/nanorc")

    return ir


@nano.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    data: dict[str, Any] = {"enable": True}

    if ir.get("nanorc"):

        def is_default_nanorc(text: str) -> bool:
            for line in text.splitlines():
                sline = line.strip()
                if not sline or sline.startswith("#"):
                    continue
                return False
            return True

        if not is_default_nanorc(ir["nanorc"]):
            data["nanorc"] = ir["nanorc"]

    return ConfigFragment(
        name="nano",
        description="nano editor",
        data={"programs.nano": data},
    )
