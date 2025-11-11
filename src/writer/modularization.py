from enum import Enum


class ModularizationLevel(Enum):
    """Writes single configuration.nix or flake.nix"""

    SINGLE_FILE = 0

    """
    Writes a modular config divided by high level modules, e.g.
        - configuration.nix
        - networking.nix
        - security.nix
        - ...
    """
    HIGH_LEVEL = 1

    """
    Writes files divided by each separate component, e.g.
        - configuration.nix
        - networking/
            - firewall.nix
            - networkManager.nix
        - security/
            - sudo.nix
            ...
    """
    COMPONENT_LEVEL = 2
