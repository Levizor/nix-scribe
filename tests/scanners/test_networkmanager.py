import pytest

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.nix_writer import raw
from nix_scribe.modules.nixos.networking.networkmanager import NetworkManager
from nix_scribe.scanners.networking.networkmanager import networkmanager

MOCK_NM_CONF = """
[main]
dns=dnsmasq
dhcp=dhclient
plugins=keyfile,ifcfg-rh

[connection]
wifi.powersave=2

[device]
wifi.scan-rand-mac-address=yes
wifi.backend=iwd
"""

MOCK_NM_CONF_D_EXTRA = """
[main]
dns=none
"""


@pytest.fixture
def nm_test_root(tmp_path):
    nm_dir = tmp_path / "etc/NetworkManager"
    conf_d = nm_dir / "conf.d"

    nm_dir.mkdir(parents=True)
    conf_d.mkdir()

    (nm_dir / "NetworkManager.conf").write_text(MOCK_NM_CONF)
    (conf_d / "extra.conf").write_text(MOCK_NM_CONF_D_EXTRA)

    return tmp_path


def test_networkmanager_scanner_disabled(nm_test_root, monkeypatch):
    context = SystemContext(nm_test_root)
    monkeypatch.setattr(context.systemctl, "is_enabled", lambda _: False)
    assert networkmanager.scan(context) is None


def test_networkmanager_scanner(nm_test_root, monkeypatch):
    context = SystemContext(nm_test_root)

    monkeypatch.setattr(
        context.systemctl, "is_enabled", lambda x: x == "NetworkManager"
    )

    mod = networkmanager.scan(context)

    assert isinstance(mod, NetworkManager)
    assert mod.enable is True
    assert mod.dns == "none"
    assert mod.dhcp is None
    assert mod.wifi is not None
    assert mod.wifi.powersave is False
    assert mod.wifi.scanRandMacAddress is True
    assert mod.wifi.backend == "iwd"
    assert mod.settings["main"]["plugins"] == "keyfile,ifcfg-rh"
    assert mod.settings["main"]["dhcp"] == "dhclient"
    assert mod.resolve_claims() == {"networkmanager"}

    fragment = mod.to_nix_fragment()
    data = fragment["networking.networkmanager"].value
    assert data["enable"] is True
    assert data["dns"] == "none"
    assert data["wifi"]["powersave"] is False
    assert data["wifi"]["scanRandMacAddress"] is True
    assert data["wifi"]["backend"] == "iwd"


def test_networkmanager_scanner_unknown_enums(tmp_path, monkeypatch):
    nm_dir = tmp_path / "etc/NetworkManager"
    nm_dir.mkdir(parents=True)
    (nm_dir / "NetworkManager.conf").write_text(
        "[main]\ndhcp=dhclient\n[connection]\nwifi.powersave=0\n"
    )

    context = SystemContext(tmp_path)
    monkeypatch.setattr(
        context.systemctl, "is_enabled", lambda x: x == "NetworkManager"
    )

    mod = networkmanager.scan(context)
    assert isinstance(mod, NetworkManager)
    assert mod.dhcp is None
    assert mod.wifi is None
    assert mod.settings["main"]["dhcp"] == "dhclient"
    assert mod.settings["connection"][raw('"wifi.powersave"')] == 0
