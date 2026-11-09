from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_module import NixModule, option
from nix_scribe.lib.registry import Scanner


class Cowsay(NixModule, prefix="environment"):
    """Fun Cowsay Plugin Module"""

    sessionVariables: dict[str, str] = option(default={})


cowsay = Scanner("fun.cowsay", description="Fun Cowsay Plugin Module")


@cowsay.scanner()
def scan(context: SystemContext) -> Cowsay | None:
    return Cowsay(
        sessionVariables={"COWSAY_MOTD": "Moo! nix-scribe plugins work like a charm!"}
    )
