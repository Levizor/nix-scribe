from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from .lib.modularization import ModularizationLevel


@dataclass
class CLIArguments:
    input_path: Path = Path("/")
    output_path: Path = Path("nix-config")
    modularization: ModularizationLevel = ModularizationLevel.SINGLE_FILE
    confirm: bool = False
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
            if not confirm(
                f"[bold yellow]Directory exists at specified output path '{output}' and contains files.[/]\nContinue?"
            ):
                raise typer.Exit(code=1)


args = CLIArguments()


def confirm(text: str, default: bool = True, console: Console | None = None) -> bool:
    if args.confirm:
        return True

    return Confirm.ask(text, default=default, console=console)
