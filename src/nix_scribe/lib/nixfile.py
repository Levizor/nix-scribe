from __future__ import annotations

import logging
from pathlib import Path

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nix_writer import NixWriter, raw
from nix_scribe.lib.option_block import BaseOptionBlock

logger = logging.getLogger(__name__)


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
        self.options: list[BaseOptionBlock] = []
        if options:
            for option in options:
                self.add_option_block(option)

    def add_import(self, imported: raw | NixFile):
        self.imports.append(imported)

    def add_option_block(self, block: BaseOptionBlock):
        self.options.append(block)
        self.arguments.update(block.arguments)

    def render(self, writer: NixWriter) -> None:
        """Main logic for writing out stuff into nix language using NixSyntaxWriter"""

        if self.description:
            writer.write_comment(self.description)

        if len(self.arguments) > 0:
            writer._writeln(f"{{{', '.join([*sorted(self.arguments), '...'])}}}:")

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

    def save(
        self,
        output_path: Path,
        modularization_level: ModularizationLevel,
        context: SystemContext,
    ):
        """
        Saves the NixFile structure to disk according to the specified
        modularization level.
        """
        config_root = output_path
        config_root.mkdir(parents=True, exist_ok=True)

        self._process_imports(config_root, modularization_level, context)

        file_path = config_root / f"{self.name}.nix"
        file_path.write_text(self.gettext())

        self._save_assets(config_root, context)

    def _process_imports(
        self,
        parent_dir: Path,
        modularization_level: ModularizationLevel,
        context: SystemContext,
    ):
        """Recursively saves child NixFiles and updates the imports list."""
        final_imports = []
        for imp in self.imports:
            if isinstance(imp, NixFile):
                import_path = imp._save_modularized(
                    parent_dir, modularization_level, context
                )
                final_imports.append(raw(import_path))
            else:
                final_imports.append(imp)
        self.imports = final_imports

    def _save_assets(self, directory: Path, context: SystemContext):
        """Copies assets from host system to the output directory."""
        for block in self.options:
            for asset in block.assets:
                dst = directory / asset.target_filename
                context.copy_file(asset.source_path, dst)

    def _save_modularized(
        self,
        parent_dir: Path,
        modularization_level: ModularizationLevel,
        context: SystemContext,
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

            self._process_imports(module_dir, modularization_level, context)

            default_nix_path = module_dir / "default.nix"
            default_nix_path.write_text(self.gettext())

            self._save_assets(module_dir, context)

            return f"./{self.name}"

        else:
            self._process_imports(parent_dir, modularization_level, context)

            file_path = parent_dir / f"{self.name}.nix"
            file_path.write_text(self.gettext())

            self._save_assets(parent_dir, context)

            return f"./{file_path.name}"
