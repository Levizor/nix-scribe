import pytest

from nix_scribe.lib.parsers.ini import parse_bool, parse_ini


def test_parse_ini():
    content = """
[section1]
key1 = value1
key2 = value2

[section2]
key3 = value3
"""
    result = parse_ini(content)
    assert result == {
        "section1": {"key1": "value1", "key2": "value2"},
        "section2": {"key3": "value3"},
    }


@pytest.mark.parametrize(
    ("val", "expected"),
    [
        (True, True),
        (False, False),
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("yes", True),
        ("YES", True),
        ("on", True),
        ("ON", True),
        ("1", True),
        (1, True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("no", False),
        ("NO", False),
        ("off", False),
        ("OFF", False),
        ("0", False),
        (0, False),
    ],
)
def test_parse_bool_valid(val, expected):
    assert parse_bool(val) is expected


@pytest.mark.parametrize(
    "val",
    [
        "unknown",
        "2",
        "3",
        None,
        [],
        {},
    ],
)
def test_parse_bool_invalid(val):
    assert parse_bool(val) is None
    assert parse_bool(val, default=True) is True
    assert parse_bool(val, default=False) is False
