from dataclasses import dataclass
from pathlib import Path

from .lib.modularization import ModularizationLevel


@dataclass
class CLIArguments:
    input_path: Path = Path("/")
    output_path: Path = Path(".")
    interactive: bool = False
    modularization: ModularizationLevel = ModularizationLevel.SINGLE_FILE
    flake: bool = False
    verbosity: int = 1
    mod_verbosity: int = 1
    no_comment: bool = False


args = CLIArguments()
