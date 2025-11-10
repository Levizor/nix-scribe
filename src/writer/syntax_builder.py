from contextlib import contextmanager
from io import StringIO

from src.arguments import args
from src.writer.value import combination, to_nix


class NixSyntaxBuilder:
    def __init__(self, indent="  "):
        self.indent = indent
        self.buffer = StringIO()
        self.level = 0

    def _indent(self, flag: bool) -> str:
        return self.indent * self.level if flag else ""

    def _write(self, text="", indent = True):
        self.buffer.write(f"{self._indent(indent)}{text}")

    def _writeln(self, line="", indent = True):
        if line:
            self._write(line, indent=indent)
        self.buffer.write("\n")

    def _write_value(self, value):
        if isinstance(value, dict):
            with self.block():
                for k, v in value.items():
                    self.write_attr(k, v)
        elif isinstance(value, combination):
            for inner_value in value:
                self._write_value(inner_value)
        elif isinstance(value, list):
            with self.block(surrounding="[]"):
                for inner_value in value:
                    self._writeln(inner_value)
        else:
            self._write(f"{to_nix(value)}", indent=False)

    def write_attr(self, key, value):
        self._write(f"{key} = ")
        self._write_value(value)
        self._writeln(";", indent=False)

    def write_dict(self, data: dict):
        for key, value in data.items():
            self.write_attr(key, value)
            self._writeln()

    def write_comment(self, comment: str):
        if not args.no_comment:
            for line in comment.splitlines():
                self._writeln(f"# {line}")


    @contextmanager
    def block(self, header="", surrounding="{}", indent = False):
        self._writeln(f"{header}{surrounding[:int(len(surrounding)/2)]}", indent)
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1
            self._write(f"{surrounding[int(len(surrounding)/2):]}")

    def gettext(self):
        return self.buffer.getvalue()

    def __str__(self):
        return self.gettext()

    def __setitem__(self, key, value):
        self.write_attr(key, value)
