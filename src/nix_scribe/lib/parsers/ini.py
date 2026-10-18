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


def parse_bool(val: Any, default: bool | None = None) -> bool | None:
    """
    Parses a boolean value from common INI boolean representations.
    """
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, str)):
        s = str(val).strip().lower()
        if s in ("true", "yes", "on", "1"):
            return True
        if s in ("false", "no", "off", "0"):
            return False
    return default
