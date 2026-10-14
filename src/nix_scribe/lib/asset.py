import re


class Asset:
    """Represents a file (copied from host or generated in-memory) to be included in the Nix configuration."""

    def __init__(
        self,
        source_path: str | None = None,
        target_filename: str | None = None,
        content: str | None = None,
    ):
        if content is not None and target_filename is None and source_path is not None:
            target_filename = source_path
            source_path = None

        if not target_filename:
            raise ValueError("Asset target_filename must not be empty.")
        if source_path is None and content is None:
            raise ValueError("Asset must specify either source_path or content.")

        self.source_path = source_path
        self.content = content
        # substitute illegal characters in the /nix/store to -
        self.target_filename = re.sub(r"[^a-zA-Z0-9\+\.\_\-\?\=]", "-", target_filename)

    @classmethod
    def from_file(cls, source_path: str, target_filename: str) -> "Asset":
        return cls(source_path=source_path, target_filename=target_filename)

    @classmethod
    def from_content(cls, target_filename: str, content: str) -> "Asset":
        return cls(target_filename=target_filename, content=content)

    def __str__(self) -> str:
        return f"./{self.target_filename}"

    def __repr__(self) -> str:
        if self.content is not None:
            return (
                f"Asset(target={self.target_filename}, content_len={len(self.content)})"
            )
        return f"Asset(source={self.source_path}, target={self.target_filename})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Asset):
            return False
        return (
            self.source_path == other.source_path
            and self.target_filename == other.target_filename
            and self.content == other.content
        )

    def __hash__(self) -> int:
        return hash((self.source_path, self.target_filename, self.content))
