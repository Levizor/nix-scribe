from nix_scribe.lib.parsers.sudoers import parse_sudoers


def test_parse_sudoers_empty():
    result = parse_sudoers("")
    assert result["defaults"] == []
    assert result["rules"] == []
    assert result["raw_lines"] == []


def test_parse_sudoers_comments_and_blanks():
    content = """
    # This is a comment
    # Another comment line

    """
    result = parse_sudoers(content)
    assert result["raw_lines"] == []
    assert result["defaults"] == []
    assert result["rules"] == []


def test_parse_sudoers_defaults():
    content = """
    Defaults env_reset
    Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    Defaults env_keep += "TERMINFO TERMINFO_DIRS"
    """
    result = parse_sudoers(content)
    assert len(result["defaults"]) == 3
    assert result["defaults"][2] == 'Defaults env_keep += "TERMINFO TERMINFO_DIRS"'


def test_parse_sudoers_rules():
    content = "%wheel ALL=(ALL:ALL) NOPASSWD: ALL\n"
    result = parse_sudoers(content)
    assert len(result["rules"]) == 1
    assert result["rules"][0] == "%wheel ALL=(ALL:ALL) NOPASSWD: ALL"


def test_parse_sudoers_custom_rules():
    content = """
    root ALL=(ALL:ALL) ALL
    alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
    %developers ALL=(ALL) /usr/bin/git
    """
    result = parse_sudoers(content)
    assert len(result["rules"]) == 3
    assert (
        result["raw_lines"][1]
        == "alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx"
    )
