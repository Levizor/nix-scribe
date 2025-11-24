from abc import ABC, abstractmethod
from typing import Any

from .nix_writer import NixWriter


class BaseOptionBlock(ABC):
    def __init__(
        self,
        name: str,
        description: str = "",
        arguments: list[str] | None = None,
    ) -> None:
        self.name = name
        self.arguments = [] if arguments is None else arguments
        self.description = description

    @abstractmethod
    def render(self, writer: NixWriter) -> None:
        pass


class SimpleOptionBlock(BaseOptionBlock):
    """
    Logical partition of a specific part of generated configuration:
        # firewall.nix

        # firewall configuration
        networking.filewall.enable = true;
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        data: dict[str, Any] | None = None,
        arguments: list[str] | None = None,
    ):
        super().__init__(name, description, arguments)
        self.data = {} if data is None else data

    def __setitem__(self, key: str, value: Any) -> None:
        self.data.__setitem__(key, value)

    def __getitem__(self, key) -> Any:
        return self.data.__getitem__(key)

    def render(self, writer: NixWriter):
        """
        Writes description at the top of the option block.
        """
        if self.description:
            writer.write_comment(self.description)

        writer.write_dict(self.data)
