from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cappa
from cappa import Arg


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

    verbose: Annotated[bool, Arg(short="-v", help="Increase verbosity.")] = False
