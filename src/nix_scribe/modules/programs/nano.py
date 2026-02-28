from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.base import BaseMapper, BaseScanner, Module


class NanoScanner(BaseScanner):
    def scan(self, context: SystemContext) -> dict[str, Any]:
        ir = {}
        enabled = bool(context.find_executable_path("nano"))

        if not enabled:
            return ir

        ir["enable"] = True

        if context.path_exists("/etc/nanorc"):
            ir["nanorc"] = context.read_file("/etc/nanorc")

        return ir


class NanoMapper(BaseMapper):
    def map(self, ir: dict[str, Any]) -> SimpleOptionBlock | None:
        if not ir.get("enable"):
            return None

        data: dict[str, Any] = {"programs.nano.enable": True}

        if ir.get("nanorc"):

            def is_default_nanorc(text: str) -> bool:
                for line in text.splitlines():
                    sline = line.strip()
                    if not sline or sline.startswith("#"):
                        continue
                    return False

                return True

            if not is_default_nanorc(ir["nanorc"]):
                data["programs.nano.nanorc"] = ir["nanorc"]

        return SimpleOptionBlock(
            name="nano",
            description="nano editor",
            data=data,
        )


module = Module("nano", NanoScanner(), NanoMapper())
