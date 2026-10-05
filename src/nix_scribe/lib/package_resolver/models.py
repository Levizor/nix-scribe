from dataclasses import dataclass


@dataclass(frozen=True)
class ResolvedPackage:
    name: str
    original_name: str
    repository: str | None = None
