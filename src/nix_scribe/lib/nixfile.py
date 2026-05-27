from __future__ import annotations

import logging
from pathlib import Path

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nix_writer import NixWriter, raw
from nix_scribe.lib.option_block import (
    CommentNode,
    ConfigFragment,
    EmptyLineNode,
    NixOptionDocument,
    OptionCollisionError,
    OptionNode,
)

logger = logging.getLogger(__name__)


class NixFile:
    def __init__(
        self,
        name: str,
        description: str = "",
        imports: list | None = None,
    ):
        self.name = name
        self.description = description

        self.arguments = set()
        self.assets: set[Asset] = set()
        self.fragments: list[ConfigFragment] = []
        self.imports: list[raw | NixFile] = [] if imports is None else imports

        self.document = NixOptionDocument()

    def add_fragment(self, fragment: ConfigFragment) -> None:
        self.fragments.append(fragment)
        self.arguments.update(fragment.arguments)
        self.assets.update(fragment.assets)

        self.document.add_header(f"--- {fragment.name}: {fragment.description} ---")

        for key, nix_node in fragment.options.items():
            try:
                self.document.add_option(key, nix_node)
            except OptionCollisionError as e:
                logger.warning(
                    f"[{self.name}.nix] Conflict in fragment '{fragment.name}'."
                    f"Keeping '{e.existing}', rejecting '{e.rejected}' for '{e.key}'"
                )
                self.document.flag_collision(e.key, e.rejected, fragment.name)

    def add_import(self, imported: raw | NixFile):
        self.imports.append(imported)

    def render(self, writer: NixWriter) -> None:
        """Main logic for writing out NixOptionDocument into nix language using NixSyntaxWriter"""

        # file description
        if self.description:
            writer.write_comment(self.description)

        # function arguments
        if len(self.arguments) > 0:
            writer._writeln(f"{{{', '.join([*sorted(self.arguments), '...'])}}}:")

        with writer.block():
            if len(self.imports) > 0:
                writer._writeln()
                writer.write_attr("imports", self.imports)
                writer._writeln()

            if len(self.document) > 0:
                for node in self.document:
                    if isinstance(node, OptionNode):
                        if node.inline_comment:
                            writer.write_comment(node.inline_comment)
                        writer.write_attr(node.key, node.value)
                    elif isinstance(node, CommentNode):
                        writer.write_comment(node.text)
                    elif isinstance(node, EmptyLineNode):
                        writer._writeln()

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
        for asset in self.assets:
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
