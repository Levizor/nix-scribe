from nix_scribe.lib.parsers.kernel import parse_modprobe, parse_modules


def test_parse_modules():
    content = """
    # /etc/modules
    tun
    kvm_intel
    """
    res = parse_modules(content)
    assert res == {"modules": ["tun", "kvm_intel"]}


def test_parse_modprobe():
    content = """
    # /etc/modprobe.d/blacklist.conf
    blacklist nouveau
    install pcspkr /bin/true
    options kvm_intel nested=1
    """
    res = parse_modprobe(content)
    assert res["blacklisted"] == ["nouveau", "pcspkr"]
    assert res["extra"] == ["options kvm_intel nested=1"]
