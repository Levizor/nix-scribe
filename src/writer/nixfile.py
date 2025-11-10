from __future__ import annotations

from pathlib import Path

from src.writer.option_block import BaseOptionBlock
from src.writer.syntax_builder import NixSyntaxBuilder
from src.writer.value import raw


class NixFile(BaseOptionBlock):
    def __init__(self, name: str, description: str | None = None):
        super().__init__(name, description)
        self.imports: list[raw | NixFile] = []
        self.options: list[BaseOptionBlock] = []

    def add_import(self, imported: raw | NixFile):
        self.imports.append(imported)

    def add_argument(self, argument: str):
        if argument not in self.arguments:
            self.arguments.append(argument)

    def add_option_block(self, block: BaseOptionBlock):
        self.options.append(block)
        for arg in block.arguments:
            self.add_argument(arg)

    def render(self, builder) -> None:
        """Main logic for writing out stuff into nix language using NixSyntaxWriter"""

        if self.description:
            builder.write_comment(self.description)

        if len(self.arguments) > 0:
            builder._writeln(f"{{{', '.join([*self.arguments, '...'])}}}:")

        with builder.block():
            if len(self.imports) > 0:
                builder._writeln()
                builder.write_attr("imports", self.imports)
                builder._writeln()

            if len(self.options) > 0:
                for option_block in self.options:
                    option_block.render(builder)

    def gettext(self) -> str:
        builder = NixSyntaxBuilder()
        self.render(builder)
        return builder.gettext()

    def save(self, path: str | None = None):
        for file in self.imports:
            if isinstance(file, NixFile):
                file.save()

        target = Path(path or self.path)
        if not target:
            raise ValueError("No output path specified.")

        target.write_text(self.gettext())
