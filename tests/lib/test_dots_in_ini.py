from nix_scribe.lib.nix_types import quote_keys_with_dots
from nix_scribe.lib.nix_writer import NixWriter
from nix_scribe.lib.parsers.ini import parse_ini


def test_dots_in_ini_keys_with_quoting():
    content = """
[connection]
wifi.powersave = 3
"""
    config = parse_ini(content)

    quoted_config = quote_keys_with_dots(config)

    writer = NixWriter()
    writer.write_attr("settings", quoted_config)
    output = writer.gettext()

    assert '"wifi.powersave" = "3";' in output
    assert "connection = {" in output
