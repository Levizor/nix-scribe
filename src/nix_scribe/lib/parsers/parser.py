from types import FunctionType
from typing import Any

from nix_scribe.lib.context import SystemContext


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Traverses a dictionary and normalizes all string values.
    """
    normalized = {}
    for k, v in config.items():
        if isinstance(v, dict):
            normalized[k] = normalize_config(v)
        elif isinstance(v, list):
            normalized[k] = [normalize_value(val) for val in v]
        else:
            normalized[k] = normalize_value(v)

    return normalized


def normalize_value(value: Any) -> bool | int | float | str | None:
    """
    Infers the real type of a string value
    """

    if not isinstance(value, str):
        return value

    lower = value.lower().strip()
    if lower == "true":
        return True
    elif lower == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


class ConfigReader:
    def __init__(self, system_context: SystemContext, parse_function: FunctionType):
        self.context = system_context
        self.parse = parse_function

    def read_config(self, path: str, is_directory_config: bool = False) -> dict:
        """
        Reads config file and parses it.
        Returns a merged config if it's specified that path is a directory.
        """
        if not is_directory_config:
            return self.parse(self.context.read_file(path))

        dir_files = self.context.read_directory_files(path)
        configs = [self.parse(file) for file in dir_files]
        merged = {}

        for config in configs:
            merged.update(config)

        return normalize_config(merged)

    def read_merge_configs_from_paths_list(self, paths: list[str]) -> dict:
        """
        Filters existing paths, parses configs and merges in the order of the list of path supplied.
        If one of the paths is a directory, all the files inside directory are treated as configs and also merged.
        """
        merged = {}

        for path in paths:
            try:
                config = self.read_config(path)
                merged.update(config)
            except FileNotFoundError:
                continue

        return merged
