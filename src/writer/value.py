def to_nix(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    elif value is None:
        return "null"
    elif isinstance(value, (int, float, raw)):
        return str(value)
    elif isinstance(value, str):
        return f'"{value}"'
    else:
        raise TypeError(f"Cannot convert {type(value)} to Nix")

class raw(str):
    def __new__(cls, value):
        return super().__new__(cls, value)
