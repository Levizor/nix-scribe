from __future__ import annotations

import logging
from pathlib import Path

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.modularization import ModularizationLevel
from nix_scribe.lib.nix_fragment import (
    CommentNode,
    EmptyLineNode,
    NixFragment,
    NixOptionDocument,
    OptionCollisionError,
    OptionNode,
)
from nix_scribe.lib.nix_writer import NixWriter, raw

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
        self.fragments: list[NixFragment] = []
        self.imports: list[raw | NixFile] = [] if imports is None else imports

        self.document = NixOptionDocument()

    def add_fragment(self, fragment: NixFragment) -> None:
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
    ) -> list[Path]:
        """
        Saves the NixFile structure to disk according to the specified
        modularization level. Returns all written file paths.
        """
        config_root = output_path
        config_root.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []
        written.extend(self._process_imports(config_root, modularization_level))

        file_path = config_root / f"{self.name}.nix"
        file_path.write_text(self.gettext())
        written.append(file_path)

        written.extend(self._save_assets(config_root))

        return list(dict.fromkeys(written))

    def _process_imports(
        self,
        parent_dir: Path,
        modularization_level: ModularizationLevel,
    ) -> list[Path]:
        """Recursively saves child NixFiles and updates the imports list."""
        final_imports = []
        written: list[Path] = []
        for imp in self.imports:
            if isinstance(imp, NixFile):
                import_path, imp_written = imp._save_modularized(
                    parent_dir, modularization_level
                )
                final_imports.append(raw(import_path))
                written.extend(imp_written)
            else:
                final_imports.append(imp)
        self.imports = final_imports
        return written

    def _save_assets(self, directory: Path) -> list[Path]:
        """Saves all registered assets to the target output directory."""
        written: list[Path] = []
        for asset in self.assets:
            dst = directory / asset.target_filename
            if isinstance(asset.content, bytes):
                dst.write_bytes(asset.content)
            else:
                dst.write_text(asset.content, encoding="utf-8")
            written.append(dst)
        return written

    def _save_modularized(
        self,
        parent_dir: Path,
        modularization_level: ModularizationLevel,
    ) -> tuple[str, list[Path]]:
        """
        Recursively saves child NixFiles for modularization levels.
        """
        written: list[Path] = []
        if modularization_level == ModularizationLevel.COMPONENT_LEVEL and any(
            isinstance(imp, NixFile) for imp in self.imports
        ):
            # create import directory and 'default.nix' with all the imports
            module_dir = parent_dir / self.name
            module_dir.mkdir(exist_ok=True)

            written.extend(self._process_imports(module_dir, modularization_level))

            default_nix_path = module_dir / "default.nix"
            default_nix_path.write_text(self.gettext())
            written.append(default_nix_path)

            written.extend(self._save_assets(module_dir))

            return f"./{self.name}", written

        else:
            written.extend(self._process_imports(parent_dir, modularization_level))

            file_path = parent_dir / f"{self.name}.nix"
            file_path.write_text(self.gettext())
            written.append(file_path)

            written.extend(self._save_assets(parent_dir))

            return f"./{file_path.name}", written
