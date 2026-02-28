from typing import Any

from nix_scribe.lib.nix_writer import raw


def quote_keys_with_dots(data: Any) -> Any:
    """
    Recursively wraps dictionary keys containing dots in 'raw' with quotes.
    This ensures that NixWriter treats them as literal identifiers instead of
    Nix attribute paths.

    Can be used for attribute set of section of an INI file nix type.
    """
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            quoted_key = k
            if isinstance(k, str) and "." in k:
                quoted_key = raw(f'"{k}"')

            result[quoted_key] = quote_keys_with_dots(v)
        return result

    if isinstance(data, list):
        return [quote_keys_with_dots(item) for item in data]

    return data
