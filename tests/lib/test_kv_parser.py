from nix_scribe.lib.parsers.kv import is_truthy, parse_kv


def test_parse_kv_dotted_keys():
    content = """
    net.ipv6.conf.all.disable_ipv6 = 1
    net.ipv6.conf.default.disable_ipv6 = true
    # comment
    """
    result = parse_kv(content)
    assert result["net.ipv6.conf.all.disable_ipv6"] == "1"
    assert result["net.ipv6.conf.default.disable_ipv6"] == "true"


def test_is_truthy():
    assert is_truthy(True) is True
    assert is_truthy(False) is False
    assert is_truthy(1) is True
    assert is_truthy(0) is False
    assert is_truthy("1") is True
    assert is_truthy("0") is False
    assert is_truthy("true") is True
    assert is_truthy("True") is True
    assert is_truthy("yes") is True
    assert is_truthy("on") is True
    assert is_truthy("false") is False
    assert is_truthy(None) is False
