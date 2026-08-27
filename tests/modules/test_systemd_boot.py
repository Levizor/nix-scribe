from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.boot.loader.systemd_boot import systemd_boot

MOCK_LOADER_CONF = """
# /boot/loader/loader.conf
default nixos-generation-1.conf
timeout 10
console-mode max
editor no
"""


MOCK_LOADER_CONF_EXTENDED = """
# /boot/loader/loader.conf
default nixos-generation-1.conf
console-mode max
editor no
sort-key custom-sort
xbootldr-mount-point /boot
"""


def test_systemd_boot_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    ir = systemd_boot.scan(context)
    assert ir == {}


def test_systemd_boot_scanner_with_files(tmp_path):
    loader_dir = tmp_path / "boot/loader"
    loader_dir.mkdir(parents=True)
    (loader_dir / "loader.conf").write_text(MOCK_LOADER_CONF_EXTENDED)

    context = SystemContext(tmp_path)
    ir = systemd_boot.scan(context)

    assert ir["enable"] is True
    assert ir["consoleMode"] == "max"
    assert ir["editor"] is False
    assert ir["sortKey"] == "custom-sort"
    assert ir["xbootldrMountPoint"] == "/boot"


def test_systemd_boot_mapper():
    assert systemd_boot.map
    mock_ir = {
        "enable": True,
        "consoleMode": "keep",
        "editor": True,
        "sortKey": "custom-sort",
        "xbootldrMountPoint": "/boot",
    }

    block = systemd_boot.map(mock_ir)
    assert isinstance(block, ConfigFragment)
    data = block["boot.loader.systemd-boot"]
    assert data["enable"] is True
    assert data["consoleMode"] == "keep"
    assert data["editor"] is True
    assert data["sortKey"] == "custom-sort"
    assert data["xbootldrMountPoint"] == "/boot"


def test_systemd_boot_mapper_empty():
    assert systemd_boot.map(None) is None
    assert systemd_boot.map({}) is None
