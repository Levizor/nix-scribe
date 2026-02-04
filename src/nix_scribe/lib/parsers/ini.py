import configparser


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
