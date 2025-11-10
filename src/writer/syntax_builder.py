from contextlib import contextmanager
from io import StringIO

from src.arguments import args
from src.writer.value import combination, to_nix


class NixSyntaxBuilder:
    def __init__(self, indent="  "):
        self.indent = indent
        self.buffer = StringIO()
        self.level = 0

    def _indent_level(self):
        return self.indent * self.level

    def _writeln(self, line=""):
        if line:
            self.buffer.write(f"{self._indent_level()}{line}\n")
        else:
            self.buffer.write("\n")

    def write_comment(self, comment: str):
        if not args.no_comment:
            for line in comment.splitlines():
                self._writeln(f"# {line}")

    def write_attr(self, key, value):
        if isinstance(value, dict):
            with self.block(f"{key} = "):
                for k, v in value.items():
                    self.write_attr(k, v)
        elif isinstance(value, combination):
            pass

        elif isinstance(value, list):
            with self.block(f"{key} = ", surrounding="[]"):
                for line in value:
                    self._writeln(to_nix(line))
        else:
            self._writeln(f"{key} = {to_nix(value)};")

    def write_dict(self, data: dict):
        for key, value in data.items():
            self.write_attr(key, value)
            self._writeln()

    @contextmanager
    def block(self, header="", semicolon=True, surrounding="{}"):
        self._writeln(f"{header}{surrounding[:int(len(surrounding)/2)]}")
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1
            self._writeln(f"{surrounding[int(len(surrounding)/2):]}{';' if semicolon else ''}")

    def gettext(self):
        return self.buffer.getvalue()

    def __str__(self):
        return self.gettext()

    def __setitem__(self, key, value):
        self.write_attr(key, value)
