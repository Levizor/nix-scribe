from pathlib import Path
from typing import Annotated

import typer

from nix_scribe.logger import setup_logging

from .arguments import args
from .lib.modularization import ModularizationLevel
from .nixscribe import NixScribe

app = typer.Typer(
    name="nix-scribe",
    help="Generate nix configuration from existing system",
    add_completion=True,
)


@app.command()
def main(
    input_path: Annotated[
        Path, typer.Option("-i", "--input", help="Path to the root directory of the OS")
    ] = Path("/"),
    output_path: Annotated[
        Path,
        typer.Option("-o", "--output", help="Output path for the configuration"),
    ] = Path("./configuration.nix"),
    modularization: Annotated[
        int,
        typer.Option(
            "-m",
            "--mod-level",
            help="Level of modularization of the configuration: 0 - single file, 1 - separate modules, 2 - separate components",
        ),
    ] = 0,
    flake: Annotated[
        bool, typer.Option("--flake", help="Write flake configuration")
    ] = False,
    no_comment: Annotated[
        bool,
        typer.Option("--no-comment", help="Don't write comments to the output files"),
    ] = False,
    interactive: Annotated[
        bool, typer.Option("--interactive", help="Run interactively")
    ] = False,
    verbosity: Annotated[
        int,
        typer.Option(
            "-v",
            "--verbosity",
            help="Set verbosity level: 0 - silent, 1 - INFO, 2 - DEBUG",
        ),
    ] = 1,
    mod_verbosity: Annotated[
        int,
        typer.Option(
            "--mod-verbosity",
            help="Set modules verbosity level: 0 - silent, 1 - INFO, 2 - DEBUG",
        ),
    ] = 1,
):
    args.input_path = input_path
    args.output_path = output_path
    args.interactive = interactive
    args.modularization = ModularizationLevel(modularization)
    args.flake = flake
    args.verbosity = verbosity
    args.mod_verbosity = mod_verbosity
    args.no_comment = no_comment

    console = setup_logging(verbosity, mod_verbosity, Path("nix-scribe.log"))

    script = NixScribe(console)
    script.run()


if __name__ == "__main__":
    app()
