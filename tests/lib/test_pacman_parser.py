from nix_scribe.lib.parsers.pacman import parse_pacman_desc

SAMPLE_PACMAN_DESC = """%NAME%
htop

%VERSION%
3.3.0-1

%BASE%
htop

%DESC%
Interactive process viewer

%URL%
https://htop.dev/

%ARCH%
x86_64

%BUILDDATE%
1700000000

%INSTALLDATE%
1705000000

%PACKAGER%
Arch Linux Packagers <packagers@archlinux.org>

%SIZE%
350000

%REASON%
0

%LICENSE%
GPL-2.0-or-later

%VALIDATION%
pgp

%DEPENDS%
ncurses
libnl

%OPTDEPENDS%
lsof: show files opened by process
strace: attach to a running process
"""


def test_parse_pacman_desc_basic():
    parsed = parse_pacman_desc(SAMPLE_PACMAN_DESC)

    assert parsed["NAME"] == "htop"
    assert parsed["VERSION"] == "3.3.0-1"
    assert parsed["BASE"] == "htop"
    assert parsed["DESC"] == "Interactive process viewer"
    assert parsed["REASON"] == "0"
    assert parsed["DEPENDS"] == ["ncurses", "libnl"]
    assert parsed["OPTDEPENDS"] == [
        "lsof: show files opened by process",
        "strace: attach to a running process",
    ]
    assert parsed["LICENSE"] == ["GPL-2.0-or-later"]


def test_parse_pacman_desc_empty_and_missing_tags():
    content = """%NAME%
curl

%REASON%
1

%OPTDEPENDS%

%DESC%
command line tool for transferring data with URLs
"""
    parsed = parse_pacman_desc(content)

    assert parsed["NAME"] == "curl"
    assert parsed["REASON"] == "1"
    assert parsed["OPTDEPENDS"] == []
    assert parsed["DESC"] == "command line tool for transferring data with URLs"
    assert "DEPENDS" not in parsed


def test_parse_pacman_desc_no_reason():
    content = """%NAME%
ripgrep

%VERSION%
14.1.0-1
"""
    parsed = parse_pacman_desc(content)

    assert parsed["NAME"] == "ripgrep"
    assert parsed["VERSION"] == "14.1.0-1"
    assert "REASON" not in parsed
