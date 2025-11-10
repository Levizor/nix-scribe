from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cappa
from cappa import Arg

from src.writer.modularization import ModularizationLevel


@cappa.command(name="nix-scribe")
@dataclass
class CLIArguments:
    input_path: Annotated[Path, Arg(help="Path to the root directory of the OS")] = (
        Path("/")
    )

    output_path: Annotated[
        Path, Arg(short="-o", long="--output", help="Output path for the configuration")
    ] = Path(".")

    interactive: Annotated[bool, Arg(short="-i", help="Run interactviely")] = False

    modularization: Annotated[
        ModularizationLevel,
        Arg(short="-m", help="Level of modularization of the configuration"),
    ] = 0

    flake: Annotated[bool, Arg(short="-f", help="Write flake configuration")] = False

    verbose: Annotated[bool, Arg(short="-v", help="Increase verbosity")] = False

    no_comment: Annotated[bool, Arg(long="--no-comment", help="Don't write comments to the output files")] = False

args = cappa.parse(CLIArguments)
