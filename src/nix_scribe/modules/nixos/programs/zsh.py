from nix_scribe.lib.nix_module import NixModule, option


class Zsh(NixModule, prefix="programs.zsh", claims={"zsh"}):
    """Zsh shell configuration"""

    enable: bool = option()
