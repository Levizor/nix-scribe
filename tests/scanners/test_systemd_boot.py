from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.boot.loader.systemd_boot import SystemdBoot
from nix_scribe.scanners.boot.loader.systemd_boot import systemd_boot

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
    assert systemd_boot.scan(context) is None


def test_systemd_boot_scanner_with_files(tmp_path):
    loader_dir = tmp_path / "boot/loader"
    loader_dir.mkdir(parents=True)
    (loader_dir / "loader.conf").write_text(MOCK_LOADER_CONF_EXTENDED)

    context = SystemContext(tmp_path)
    mod = systemd_boot.scan(context)

    assert isinstance(mod, SystemdBoot)
    assert mod.enable is True
    assert mod.consoleMode == "max"
    assert mod.editor is False
    assert mod.sortKey == "custom-sort"
    assert mod.xbootldrMountPoint == "/boot"

    fragment = mod.to_nix_fragment()
    data = fragment["boot.loader.systemd-boot"].value
    assert data["enable"] is True
    assert data["consoleMode"] == "max"
    assert data["editor"] is False
    assert data["sortKey"] == "custom-sort"
    assert data["xbootldrMountPoint"] == "/boot"
