from __future__ import annotations

import re


class Asset:
    """Represents an in-memory file asset (text or binary) to be included in the Nix configuration."""

    def __init__(self, target_filename: str, content: str | bytes):
        if not target_filename:
            raise ValueError("Asset target_filename must not be empty.")
        # substitute illegal characters in the /nix/store to -
        self.target_filename = re.sub(r"[^a-zA-Z0-9\+\.\_\-\?\=]", "-", target_filename)
        self.content = content

    def __str__(self) -> str:
        return f"./{self.target_filename}"

    def __repr__(self) -> str:
        return f"Asset(target={self.target_filename}, content_len={len(self.content)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Asset):
            return False
        return (
            self.target_filename == other.target_filename
            and self.content == other.content
        )

    def __hash__(self) -> int:
        return hash((self.target_filename, self.content))
