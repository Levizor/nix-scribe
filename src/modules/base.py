from abc import abstractmethod

from lib.context import SystemContext
from lib.option_block import BaseOptionBlock


class BaseScanner:
    @abstractmethod
    def scan(self, context: SystemContext) -> dict:
        """
        Performs the scan and returns the Intermediate Representation.
        """
        pass


class BaseMapper:
    @abstractmethod
    def map(self, ir: dict) -> BaseOptionBlock | None:
        """
        Takes the Intermediate Representation (IR) and returns an OptionBlock containing the NixOS configuration or None.
        """
        pass


class Module:
    def __init__(self, name: str, scanner: BaseScanner, mapper: BaseMapper) -> None:
        self.name = name
        self.scanner = scanner
        self.mapper = mapper
        self.ir: dict = {}
        self.option_block: BaseOptionBlock | None = None

    def run_scan(self, context: SystemContext):
        self.ir = self.scanner.scan(context)

    def run_map(self):
        self.option_block = self.mapper.map(self.ir)
