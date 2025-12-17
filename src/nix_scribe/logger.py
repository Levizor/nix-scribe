import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


class RichColorFormatter(logging.Formatter):
    """
    Wraps log messages in Rich color tags based on the log level.
    """

    def format(self, record):
        msg = super().format(record)
        if record.levelno >= logging.ERROR:
            return f"[red]{msg}[/]"
        elif record.levelno >= logging.WARNING:
            return f"[yellow]{msg}[/]"
        return msg


class ModuleNameFilter(logging.Filter):
    """
    Injects a short_name attribute into log records
    Transforms 'src.nix_scribe.modules.nixo'
    """

    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        name = record.name
        marker = ".modules."

        idx = name.find(marker)
        if idx != -1:
            record.short_name = name[idx + len(marker) :]
        else:
            record.short_name = name

        return True


def get_level(leveln: int):
    level = logging.INFO
    if leveln <= 0:
        level = logging.ERROR
    elif leveln >= 2:
        level = logging.DEBUG
    return level


def setup_logging(
    verbosity: int = 1, mod_verbosity: int = 1, log_file: Path | None = None
):
    """
    Configures split logging:
        - Root: File logging
        - core: nix-scribe console logging
        - mod: modules console logging
    verbosity: 0 = Silent (Error only), 1 = Info (Default), 2 = Debug
    log_file: optional path to write plain text logs
    """
    console = Console(stderr=True)

    core_level = get_level(verbosity)
    mod_level = get_level(mod_verbosity)

    # Root logger
    root_handlers = []

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        root_handlers.append(file_handler)

    logging.root.handlers.clear()

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)s - $(levelname)s: %(message)s",
        handlers=root_handlers,
        force=True,
    )

    # Core logger
    core_logger = logging.getLogger("nix_scribe")
    core_logger.setLevel(core_level)
    core_logger.propagate = True

    core_console = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_time=False,
        show_level=False,
        show_path=False,
    )
    core_console.setFormatter(RichColorFormatter("%(message)s"))
    core_logger.addHandler(core_console)

    # Modules logger
    mod_logger = logging.getLogger("nix_scribe.modules")
    mod_logger.setLevel(mod_level)
    mod_logger.propagate = True

    mod_console = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_time=False,
        show_level=False,
        show_path=False,
    )

    mod_console.addFilter(ModuleNameFilter())
    mod_console.setFormatter(
        RichColorFormatter("[grey50]%(short_name)s[/]: %(message)s")
    )

    mod_logger.addHandler(mod_console)

    return console
