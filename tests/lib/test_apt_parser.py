from nix_scribe.lib.parsers.apt import (
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
