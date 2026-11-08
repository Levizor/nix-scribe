import os
from dataclasses import dataclass, field
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from .lib.modularization import ModularizationLevel


@dataclass
class CLIArguments:
    root_path: Path = Path("/")
    output_path: Path = Path("nix-config")
    modularization: ModularizationLevel = ModularizationLevel.SINGLE_FILE
    confirm: bool = False
    verbosity: int = 1
    mod_verbosity: int = 1
    no_comment: bool = False
    keep_defaults: bool = False
    enable_modules: list[str] = field(default_factory=list)
    disable_modules: list[str] = field(default_factory=list)
    only_modules: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    log_file: Path | None = None
    no_log_file: bool = False
    dump_ir: bool = False

    def check(self):
        output = self.output_path
        if output.exists() and output.is_file():
            raise typer.BadParameter(
                f"File exists at specified path: '{output}'", param_hint="output_path"
            )

        check_path = output
        while not check_path.exists() and check_path.parent != check_path:
            check_path = check_path.parent

        if not os.access(check_path, os.W_OK):
            styled_output = typer.style(
                f"'{output}'", fg=typer.colors.YELLOW, bold=True
            )
            raw_cmd = f"'sudo chown -R $USER:$USER {output}'"
            styled_cmd = " ".join(
                typer.style(w, fg=typer.colors.CYAN, bold=True)
                for w in raw_cmd.split(" ")
            )
            raise typer.BadParameter(
                f"Output directory {styled_output} is not writable.\nDid you previously run with sudo? Fix permissions with {styled_cmd}.",
                param_hint="output_path",
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
