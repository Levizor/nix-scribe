import configparser
from typing import Any


def parse_ini(content: str, preserve_case: bool = True) -> dict[str, dict[str, str]]:
    """
    Parses INI configuration into a nested dictionary
    """

    parser = configparser.ConfigParser()

    if preserve_case:
        parser.optionxform = str

    try:
        parser.read_string(content)
    except configparser.Error:
        raise

    return {section: dict(parser.items(section)) for section in parser.sections()}


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
