from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

from nix_scribe.lib.context import SystemContext


class Asset(ABC):
    """Abstract base class for assets to be included in the Nix configuration."""

    def __init__(self, target_filename: str):
        if not target_filename:
            raise ValueError("Asset target_filename must not be empty.")
        # substitute illegal characters in the /nix/store to -
        self.target_filename = re.sub(r"[^a-zA-Z0-9\+\.\_\-\?\=]", "-", target_filename)

    @classmethod
    def from_file(cls, source_path: str, target_filename: str) -> FileAsset:
        return FileAsset(source_path=source_path, target_filename=target_filename)

    @classmethod
    def from_content(cls, target_filename: str, content: str | bytes) -> ContentAsset:
        return ContentAsset(target_filename=target_filename, content=content)

    def __str__(self) -> str:
        return f"./{self.target_filename}"

    @abstractmethod
    def save(self, directory: Path, context: SystemContext) -> None:
        """Saves this asset into the destination directory."""
        pass


class FileAsset(Asset):
    """An asset copied from the target host filesystem."""

    def __init__(self, source_path: str, target_filename: str):
        if not source_path:
            raise ValueError("FileAsset source_path must not be empty.")
        super().__init__(target_filename)
        self.source_path = source_path

    def save(self, directory: Path, context: SystemContext) -> None:
        dst = directory / self.target_filename
        context.copy_file(self.source_path, dst)

    def __repr__(self) -> str:
        return f"FileAsset(source={self.source_path}, target={self.target_filename})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileAsset):
            return False
        return (
            self.source_path == other.source_path
            and self.target_filename == other.target_filename
        )

    def __hash__(self) -> int:
        return hash((self.source_path, self.target_filename))


class ContentAsset(Asset):
    """An asset generated in-memory as text or bytes."""

    def __init__(self, target_filename: str, content: str | bytes):
        super().__init__(target_filename)
        self.content = content

    def save(self, directory: Path, context: SystemContext) -> None:
        dst = directory / self.target_filename
        if isinstance(self.content, bytes):
            dst.write_bytes(self.content)
        else:
            dst.write_text(self.content, encoding="utf-8")

    def __repr__(self) -> str:
        return f"ContentAsset(target={self.target_filename}, content_len={len(self.content)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContentAsset):
            return False
        return (
            self.target_filename == other.target_filename
            and self.content == other.content
        )

    def __hash__(self) -> int:
        return hash((self.target_filename, self.content))
