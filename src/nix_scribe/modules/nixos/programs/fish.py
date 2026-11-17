from nix_scribe.lib.nix_module import NixModule, option


class Fish(NixModule, prefix="programs.fish", claims={"fish"}):
    """Fish shell configuration"""

    enable: bool = option()
