from nix_scribe.lib.parsers.apt import (
    AptHistoryPackage,
    parse_apt_history,
    parse_deb822,
    parse_debian_relationship_packages,
    parse_dpkg_status,
    parse_extended_states,
)

SAMPLE_EXTENDED_STATES = """
# Extended states file
Package: ripgrep
Architecture: amd64
Auto-Installed: 0

Package: libssl3
Architecture: amd64
Auto-Installed: 1

Package: batcat
Architecture: amd64
Auto-Installed: 0

Package: removed-tool
Architecture: amd64
Auto-Installed: 0
"""

SAMPLE_DPKG_STATUS = """
Package: ripgrep
Status: install ok installed
Priority: optional
Section: utils
Architecture: amd64
Version: 14.1.0-1
Description: Fast line-oriented regex search tool
 ripgrep is a line-oriented search tool that recursively
 searches your current directory for a regex pattern.
 .
 More details here.

Package: libssl3
Status: install ok installed
Priority: optional
Section: libs
Architecture: amd64
Version: 3.0.13-0ubuntu3.4

Package: batcat
Status: install ok installed
Priority: optional
Section: utils
Architecture: amd64
Version: 0.24.0

Package: removed-tool
Status: deinstall ok config-files
Priority: optional
Section: utils
Architecture: amd64
Version: 1.0.0

Package: coreutils
Status: install ok installed
Priority: required
Section: utils
Architecture: amd64
Version: 9.4-3ubuntu6
"""


def test_parse_deb822_basic():
    content = """
Package: foo
Version: 1.0

Package: bar
Version: 2.0
"""
    records = parse_deb822(content)
    assert len(records) == 2
    assert records[0] == {"Package": "foo", "Version": "1.0"}
    assert records[1] == {"Package": "bar", "Version": "2.0"}


def test_parse_deb822_multiline():
    content = """
Package: multiline
Description: First line summary
 second line text
 .
 fourth line text after blank
"""
    records = parse_deb822(content)
    assert len(records) == 1
    desc = records[0]["Description"]
    assert (
        "First line summary\nsecond line text\n\nfourth line text after blank" in desc
    )


def test_parse_extended_states():
    parsed = parse_extended_states(SAMPLE_EXTENDED_STATES)
    assert len(parsed) == 4
    assert parsed["ripgrep"]["Auto-Installed"] == "0"
    assert parsed["libssl3"]["Auto-Installed"] == "1"


def test_parse_dpkg_status():
    parsed = parse_dpkg_status(SAMPLE_DPKG_STATUS)
    assert len(parsed) == 5
    assert parsed["ripgrep"]["Status"] == "install ok installed"
    assert parsed["removed-tool"]["Status"] == "deinstall ok config-files"
    assert parsed["coreutils"]["Priority"] == "required"


def test_parse_debian_relationship_packages():
    line = "firefox | firefox-esr, libreoffice (>= 7.0), thunderbird:amd64 [linux-any]"
    packages = parse_debian_relationship_packages(line)
    assert packages == ["firefox", "firefox-esr", "libreoffice", "thunderbird"]


def test_parse_apt_history():
    content = """
Start-Date: 2026-10-14  17:04:43
Commandline: apt-get install -y curl fastfetch
Install: libkeyutils1:amd64 (1.6.3-6ubuntu3, automatic), fastfetch:amd64 (2.57.1+dfsg-1ubuntu1), curl (8.18.0)
End-Date: 2026-10-14  17:04:46

Start-Date: 2026-10-14  18:00:00
Commandline: apt remove fastfetch
Remove: fastfetch:amd64 (2.57.1+dfsg-1ubuntu1)
End-Date: 2026-10-14  18:00:05
"""
    records = parse_apt_history(content)
    assert len(records) == 2

    assert records[0].start_date == "2026-10-14  17:04:43"
    assert records[0].commandline == "apt-get install -y curl fastfetch"
    assert records[0].end_date == "2026-10-14  17:04:46"
    assert records[0].install == [
        AptHistoryPackage(
            name="libkeyutils1",
            version="1.6.3-6ubuntu3",
            architecture="amd64",
            flags=("automatic",),
        ),
        AptHistoryPackage(
            name="fastfetch",
            version="2.57.1+dfsg-1ubuntu1",
            architecture="amd64",
            flags=(),
        ),
        AptHistoryPackage(
            name="curl",
            version="8.18.0",
            architecture=None,
            flags=(),
        ),
    ]

    assert records[1].commandline == "apt remove fastfetch"
    assert records[1].remove == [
        AptHistoryPackage(
            name="fastfetch",
            version="2.57.1+dfsg-1ubuntu1",
            architecture="amd64",
            flags=(),
        )
    ]
