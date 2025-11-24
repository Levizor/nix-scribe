from pathlib import Path
from typing import Annotated

import typer

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
    verbose: Annotated[bool, typer.Option("-v", help="Increase verbosity")] = False,
):
    args.input_path = input_path
    args.output_path = output_path
    args.interactive = interactive
    args.modularization = ModularizationLevel(modularization)
    args.flake = flake
    args.verbose = verbose
    args.no_comment = no_comment
    script = NixScribe()
    script.run()


if __name__ == "__main__":
    app()
