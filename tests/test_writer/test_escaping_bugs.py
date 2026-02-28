from nix_scribe.lib.nix_writer import NixWriter


def test_multiline_escaping_of_double_single_quotes():
    writer = NixWriter()
    writer._write_value("two single quotes: ''\n")
    expected = "''\n  two single quotes: '''\n''"
    assert writer.gettext() == expected


def test_multiline_escaping_of_triple_single_quotes():
    writer = NixWriter()
    writer._write_value("three single quotes: '''\n")
    expected = "''\n  three single quotes: ''''\n''"
    assert writer.gettext() == expected


def test_interpolation_in_single_line():
    writer = NixWriter()
    writer._write_value("hello ${debian_chroot}")
    assert writer.gettext() == r'"hello \${debian_chroot}"'


def test_interpolation_in_multi_line():
    writer = NixWriter()
    writer._write_value("hello ${debian_chroot}\n")
    expected = "''\n  hello " + '${"$"}{' + "debian_chroot}\n''"
    assert writer.gettext() == expected


def test_single_line_with_quotes_and_interpolation():
    writer = NixWriter()
    writer._write_value("PS1='${debian_chroot}'")
    expected = "\"PS1='\\${debian_chroot}'\""
    assert writer.gettext() == expected
