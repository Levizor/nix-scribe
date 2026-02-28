from nix_scribe.lib.nix_writer import NixWriter


def test_interpolation_escaping_single_line():
    writer = NixWriter()
    writer._write_value("hello ${debian_chroot}")
    assert writer.gettext() == r'"hello \${debian_chroot}"'


def test_interpolation_escaping_multi_line():
    writer = NixWriter()
    writer._write_value("line1\nline2 ${var}")
    expected = "''\n  line1\n  line2 " + '${"$"}{' + "var}\n''"
    assert writer.gettext() == expected
