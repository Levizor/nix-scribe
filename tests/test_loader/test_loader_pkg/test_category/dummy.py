from nix_scribe.lib.registry import Module

dummy = Module("dummy")


@dummy.scanner()
def scan(context):
    return {}


@dummy.mapper()
def map(ir):
    return None
