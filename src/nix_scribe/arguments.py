from dataclasses import dataclass
from pathlib import Path

import typer

from .lib.modularization import ModularizationLevel


@dataclass
class CLIArguments:
    input_path: Path = Path("/")
    output_path: Path = Path("nix-config")
    interactive: bool = False
    modularization: ModularizationLevel = ModularizationLevel.SINGLE_FILE
    flake: bool = False
    verbosity: int = 1
    mod_verbosity: int = 1
    no_comment: bool = False

    def check(self):
        output = self.output_path
        if output.exists() and output.is_file():
            raise typer.BadParameter(
                f"File exists at specified path: '{output}'", param_hint="output_path"
            )

        if (
            output.exists()
            and output.is_dir()
            and any(item for item in output.iterdir() if not item.name.startswith("."))
        ):
            if not typer.confirm(
                f"Directory exists at specified output path '{output}' and contains files.\nContinue?"
            ):
                raise typer.Exit(code=1)


args = CLIArguments()
