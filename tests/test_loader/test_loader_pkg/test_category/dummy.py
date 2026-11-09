from nix_scribe.lib.registry import Scanner

dummy = Scanner("dummy")


@dummy.scanner()
def scan(context):
    return None
