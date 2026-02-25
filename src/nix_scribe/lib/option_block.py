from abc import ABC, abstractmethod
from typing import Any

from .asset import Asset
from .nix_writer import NixWriter


class BaseOptionBlock(ABC):
    """
    Logical partition of a specific part of generated configuration:
        name - used as file name
        description - used for comments
        arguments - required arguments for the option block, e.g. pkgs, lib, etc.
        assets - files that must be copied to the configuration from the target system
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        arguments: list[str] | None = None,
    ) -> None:
        self.name = name
        self.arguments = [] if arguments is None else arguments
        self.description = description
        self.assets: set[Asset] = set()

    def register_asset(self, asset: Asset) -> Asset:
        """
        Explicitly registers an asset.
        Returns the asset for convenient use in assignment.
        """
        self.assets.add(asset)
        return asset

    @abstractmethod
    def render(self, writer: NixWriter) -> None:
        pass


class SimpleOptionBlock(BaseOptionBlock):
    """
    Outputs a description comment and all the options specified.
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
        self.data: dict[str, Any] = {}
        if data:
            for k, v in data.items():
                self[k] = v

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Sets a value in the data dict and automatically registers assets.
        """
        self._register_potential_assets(value)
        self.data.__setitem__(key, value)

    def _register_potential_assets(self, value: Any) -> None:
        """
        Recursively finds and registers assets in the value being set.
        """
        if isinstance(value, Asset):
            self.register_asset(value)
        elif isinstance(value, dict):
            for v in value.values():
                self._register_potential_assets(v)
        elif isinstance(value, list):
            for v in value:
                self._register_potential_assets(v)

    def __getitem__(self, key) -> Any:
        return self.data.__getitem__(key)

    def render(self, writer: NixWriter):
        """
        Writes description at the top of the option block.
        """
        if self.description:
            writer.write_comment(self.description)

        writer.write_dict(self.data)
