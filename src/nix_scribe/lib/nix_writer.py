from contextlib import contextmanager
from io import StringIO
from typing import Any, Generator

from nix_scribe.arguments import args
from nix_scribe.lib.asset import Asset


class raw(str):
    def __new__(cls, value):
        return super().__new__(cls, value)

    def __repr__(self):
        return str(self)


class combination(list):
    def __new__(cls, *args):
        return super().__new__(cls, *args)

    def __repr__(self):
        return "".join(repr(item) for item in self)


def nix_with(with_attr: str, value) -> combination:
    return combination([raw(f"with {with_attr}; "), value])


def with_pkgs(*args):
    return nix_with("pkgs", [raw(p) for p in args])


class NixWriter:
    def __init__(self, indent="  "):
        self.indent = indent
        self.buffer = StringIO()
        self.level = 0

    def _indent(self) -> str:
        return self.indent * self.level

    def _write_raw(self, text):
        self.buffer.write(text)

    def _write(self, text=""):
        self._write_raw(f"{self._indent()}{text}")

    def _writeln(self, line=""):
        if line:
            self._write(line)
        self.buffer.write("\n")

    def _write_value(self, value: Any):
        if isinstance(value, bool):
            self._write_raw("true" if value else "false")

        elif value is None:
            self._write_raw("null")

        elif isinstance(value, (int, float, raw)):
            self._write_raw(str(value))

        elif isinstance(value, Asset):
            self._write_raw(f"./{value.target_filename}")

        elif isinstance(value, combination):
            for inner_value in value:
                self._write_value(inner_value)

        elif isinstance(value, str):
            if "\n" in value:
                value = value.replace("''", "'''").replace("${", "''${")
                with self.block(surrounding="''''"):
                    for line in value.splitlines():
                        self._writeln(line)
            else:
                value = value.replace("${", "\\${")
                self._write_raw(f'"{value}"')

        elif isinstance(value, dict):
            with self.block():
                for k, v in value.items():
                    self.write_attr(k, v)

        elif isinstance(value, list):
            with self.block(surrounding="[]"):
                for inner_value in value:
                    self._write()
                    self._write_value(inner_value)
                    self._writeln()

        else:
            raise TypeError(f"Cannot convert {type(value)} to Nix")

    def write_attr(self, key, value):
        self._write(f"{key} = ")
        self._write_value(value)
        self._write_raw(";\n")

    def write_dict(self, data: dict):
        for key, value in data.items():
            self.write_attr(key, value)
            self._writeln()

    def write_comment(self, comment: str):
        if not args.no_comment:
            for line in comment.splitlines():
                self._writeln(f"# {line}")

    @contextmanager
    def block(self, header="", surrounding="{}") -> Generator:
        self._write_raw(f"{header}{surrounding[: int(len(surrounding) / 2)]}\n")
        self.level += 1
        try:
            yield self
        finally:
            self.level -= 1
            self._write(f"{surrounding[int(len(surrounding) / 2) :]}")

    def gettext(self):
        return self.buffer.getvalue()

    def clear(self):
        self.buffer = StringIO()
        self.level = 0

    def __str__(self):
        return self.gettext()

    def __setitem__(self, key, value):
        self.write_attr(key, value)
