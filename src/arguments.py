from dataclasses import dataclass
from pathlib import Path

from lib.modularization import ModularizationLevel


@dataclass
class CLIArguments:
    input_path: Path = Path("/")
    output_path: Path = Path(".")
    interactive: bool = False
    modularization: ModularizationLevel = ModularizationLevel.SINGLE_FILE
    flake: bool = False
    verbose: bool = False
    no_comment: bool = False


args = CLIArguments()
