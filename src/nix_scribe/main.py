import logging
from pathlib import Path
from typing import Annotated

import typer

from nix_scribe.lib.loader import ModuleLoader
from nix_scribe.lib.registry import (
    InvalidModuleError,
    ModuleFilter,
    ModuleRegistry,
    print_modules_table,
    print_modules_tree,
)
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
    root_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the root directory of the system to be scanned",
        ),
    ] = Path("/"),
    output_path: Annotated[
        Path,
        typer.Option("-o", "--output", help="Output path for the configuration"),
    ] = Path("./nix-config"),
    modularization: Annotated[
        int,
        typer.Option(
            "-m",
            "--mod-level",
            help="Level of modularization of the configuration: 0 - single file, 1 - separate modules, 2 - separate components",
        ),
    ] = 0,
    no_comment: Annotated[
        bool,
        typer.Option("--no-comment", help="Don't write comments to the output files"),
    ] = False,
    confirm: Annotated[
        bool, typer.Option("--confirm", help="Don't ask for confirmation")
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
        int | None,
        typer.Option(
            "--mod-verbosity",
            help="Set modules verbosity level: 0 - silent, 1 - INFO, 2 - DEBUG",
        ),
    ] = None,
    enable_module: Annotated[
        list[str] | None,
        typer.Option(
            "-e",
            "--enable-module",
            help="Enable/whitelist specific module(s) (comma-separated or repeated flags)",
        ),
    ] = None,
    disable_module: Annotated[
        list[str] | None,
        typer.Option(
            "-d",
            "--disable-module",
            help="Disable/blacklist specific module(s) (comma-separated or repeated flags)",
        ),
    ] = None,
    only: Annotated[
        list[str] | None,
        typer.Option(
            "--only",
            help="Only run specific module(s) (comma-separated or repeated flags)",
        ),
    ] = None,
    plugin: Annotated[
        list[str] | None,
        typer.Option(
            "-p",
            "--plugin",
            help="Load plugin Python package location or file/directory path (comma-separated or repeated flags)",
        ),
    ] = None,
    list_modules: Annotated[
        bool,
        typer.Option(
            "--list-modules",
            help="List all available modules and their default states, then exit",
        ),
    ] = False,
    list_modules_tree: Annotated[
        bool,
        typer.Option(
            "--list-modules-tree",
            help="List all available modules in a hierarchical tree view, then exit",
        ),
    ] = False,
):
    args.root_path = root_path
    args.output_path = output_path
    args.modularization = ModularizationLevel(modularization)
    args.verbosity = verbosity
    args.mod_verbosity = verbosity if not mod_verbosity else mod_verbosity
    args.no_comment = no_comment
    args.confirm = confirm
    args.enable_modules = enable_module or []
    args.disable_modules = disable_module or []
    args.only_modules = only or []
    args.plugins = ModuleFilter._parse(plugin)

    console = setup_logging(args.verbosity, args.mod_verbosity, Path("nix-scribe.log"))
    log = logging.getLogger(__name__)
    log.debug(args)

    loader = ModuleLoader()
    valid_modules = loader.discover()

    for plugin_item in args.plugins:
        try:
            path = Path(plugin_item)
            if "/" in plugin_item or plugin_item.endswith(".py") or path.exists():
                plugin_loader = ModuleLoader(modules_package=None, path=path)
            else:
                plugin_loader = ModuleLoader(modules_package=plugin_item)
            valid_modules.update(plugin_loader.discover())
        except (ImportError, FileNotFoundError) as e:
            raise typer.BadParameter(
                f"Failed to load plugin '{plugin_item}': {e}"
            ) from e

    filter_spec = ModuleFilter.from_raw(
        enable=args.enable_modules,
        disable=args.disable_modules,
        only=args.only_modules,
    )

    try:
        if list_modules_tree:
            print_modules_tree(console, modules=valid_modules, filter_spec=filter_spec)
            raise typer.Exit(code=0)

        if list_modules:
            print_modules_table(console, modules=valid_modules, filter_spec=filter_spec)
            raise typer.Exit(code=0)

        args.check()

        active_modules = ModuleRegistry().filter(
            modules=valid_modules, filter_spec=filter_spec
        )

        script = NixScribe(console, modules=active_modules)
        script.run()
    except InvalidModuleError as e:
        raise typer.BadParameter(str(e)) from e


if __name__ == "__main__":
    app()
