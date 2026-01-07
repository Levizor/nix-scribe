from __future__ import annotations

from pathlib import Path

from nix_scribe.lib.modularization import ModularizationLevel
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
        self.options = []
        if options:
            for option in options:
                self.add_option_block(option)

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

    def save(self, output_path: Path, modularization_level: ModularizationLevel):
        """
        Saves the NixFile structure to disk according to the specified
        modularization level.
        """
        config_root = output_path
        file_path = config_root / f"{self.name}.nix"

        config_root.mkdir(parents=True, exist_ok=True)

        imports = list(self.imports)
        final_imports = []

        for imp in imports:
            # handle NixFile in imports
            if isinstance(imp, NixFile):
                import_path = imp._save_modularized(config_root, modularization_level)
                final_imports.append(raw(import_path))
            else:
                final_imports.append(imp)

        self.imports = final_imports
        file_path.write_text(self.gettext())

    def _save_modularized(
        self, parent_dir: Path, modularization_level: ModularizationLevel
    ) -> str:
        """
        Recursively saves child NixFiles for modularization levels.
        """
        if modularization_level == ModularizationLevel.COMPONENT_LEVEL and any(
            isinstance(imp, NixFile) for imp in self.imports
        ):
            # create import directory and 'default.nix' with all the imports
            module_dir = parent_dir / self.name
            module_dir.mkdir(exist_ok=True)

            default_nix_path = module_dir / "default.nix"

            imports_to_process = list(self.imports)
            final_imports = []
            for imp in imports_to_process:
                if isinstance(imp, NixFile):
                    import_path = imp._save_modularized(
                        module_dir, modularization_level
                    )
                    final_imports.append(raw(import_path))
                else:
                    final_imports.append(imp)

            self.imports = final_imports
            default_nix_path.write_text(self.gettext())

            return f"./{self.name}"

        else:
            file_path = parent_dir / f"{self.name}.nix"
            file_path.write_text(self.gettext())
            return f"./{file_path.name}"
