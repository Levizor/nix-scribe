from nix_scribe.lib.nix_writer import NixWriter


def test_interpolation_with_preceding_quote_bug_fix():
    writer = NixWriter()
    input_str = "PS1='${debian_chroot}\n"
    writer._write_value(input_str)

    result = writer.gettext()

    assert 'PS1=\'${"$"}{debian_chroot}' in result
    assert "'''${" not in result
