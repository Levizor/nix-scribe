class Asset:
    """
    Represents a file from the host system that should be copied into the
    generated Nix configuration.
    """

    def __init__(self, source_path: str, target_filename: str):
        self.source_path = source_path
        self.target_filename = target_filename

    def __repr__(self):
        return f"Asset(source={self.source_path}, target={self.target_filename})"

    def __eq__(self, other):
        if not isinstance(other, Asset):
            return False
        return (
            self.source_path == other.source_path
            and self.target_filename == other.target_filename
        )

    def __hash__(self):
        return hash((self.source_path, self.target_filename))
