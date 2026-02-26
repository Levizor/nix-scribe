import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.networking.networkmanager import (
    NetworkManagerMapper,
    NetworkManagerScanner,
)

MOCK_NM_CONF = """
[main]
dns=dnsmasq
dhcp=dhclient
plugins=keyfile,ifcfg-rh

[connection]
wifi.powersave=2

[device]
wifi.scan-rand-mac-address=yes
"""

MOCK_NM_CONF_D_EXTRA = """
[main]
dns=none
"""


@pytest.fixture
def nm_test_root(tmp_path):
    """
    Creates a temporary NetworkManager configuration structure.
    """
    nm_dir = tmp_path / "etc/NetworkManager"
    conf_d = nm_dir / "conf.d"

    nm_dir.mkdir(parents=True)
    conf_d.mkdir()

    (nm_dir / "NetworkManager.conf").write_text(MOCK_NM_CONF)
    (conf_d / "extra.conf").write_text(MOCK_NM_CONF_D_EXTRA)

    return tmp_path


def test_networkmanager_scanner(nm_test_root, monkeypatch):
    context = SystemContext(nm_test_root)

    monkeypatch.setattr(
        context.systemctl, "is_enabled", lambda x: x == "NetworkManager"
    )

    scanner = NetworkManagerScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    config = ir["config"]

    # verify deep merging
    assert config["main"]["dns"] == "none"
    assert config["main"]["dhcp"] == "dhclient"
    assert config["connection"]["wifi.powersave"] == 2
    assert config["device"]["wifi.scan-rand-mac-address"] == "yes"
    assert config["main"]["plugins"] == "keyfile,ifcfg-rh"


def test_networkmanager_mapper():
    mock_ir = {
        "enable": True,
        "config": {
            "main": {"dns": "dnsmasq", "dhcp": "dhclient", "plugins": "keyfile"},
            "connection": {"wifi.powersave": 2},
            "device": {"wifi.scan-rand-mac-address": True},
        },
    }

    mapper = NetworkManagerMapper()
    block = mapper.map(mock_ir)

    assert isinstance(block, SimpleOptionBlock)
    data = block.data["networking"]["networkmanager"]
    assert data["enable"] is True
    assert data["dns"] == "dnsmasq"
    assert data["dhcp"] == "dhclient"
    assert data["wifi"]["powersave"] == 2
    assert data["wifi"]["scanRandMacAddress"] is True
    assert data["settings"]["main"]["plugins"] == "keyfile"


def test_networkmanager_mapper_disabled():
    mock_ir = {"enable": False}
    mapper = NetworkManagerMapper()
    block = mapper.map(mock_ir)
    assert block is None
