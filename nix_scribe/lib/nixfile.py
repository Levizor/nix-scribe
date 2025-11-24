from __future__ import annotations

from pathlib import Path

from nix_scribe.lib.nix_writer import NixWriter, raw
from nix_scribe.lib.option_block import BaseOptionBlock


class NixFile(BaseOptionBlock):
    def __init__(
        self,
        name: str,
        description: str = "",
        imports: list | None = None,
        options: list | None = None,
    ):
        super().__init__(name, description)
        self.imports: list[raw | NixFile] = [] if imports is None else imports
        self.options: list[BaseOptionBlock] = [] if options is None else options

    def add_import(self, imported: raw | NixFile):
        self.imports.append(imported)

    def add_argument(self, argument: str):
        if argument not in self.arguments:
            self.arguments.append(argument)

    def add_option_block(self, block: BaseOptionBlock):
        self.options.append(block)
        for arg in block.arguments:
            self.add_argument(arg)

    def render(self, writer: NixWriter) -> None:
        """Main logic for writing out stuff into nix language using NixSyntaxWriter"""

        if self.description:
            writer.write_comment(self.description)

        if len(self.arguments) > 0:
            writer._writeln(f"{{{', '.join([*self.arguments, '...'])}}}:")

        with writer.block():
            if len(self.imports) > 0:
                writer._writeln()
                writer.write_attr("imports", self.imports)
                writer._writeln()

            if len(self.options) > 0:
                for option_block in self.options:
                    option_block.render(writer)

    def gettext(self) -> str:
        writer = NixWriter()
        self.render(writer)
        return writer.gettext()

    def save(self, path: Path | None = None):
        for file in self.imports:
            if isinstance(file, NixFile):
                file.save()

        if path and path.is_dir():
            path = path / (self.name + ".nix")

        target = path or Path(self.name + ".nix")
        if not target:
            raise ValueError("No output path specified.")

        target.write_text(self.gettext())
