import unittest.mock

from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.boot.loader.grub import GrubMapper, GrubScanner


def test_grub_scanner_efi():
    mock_context = unittest.mock.MagicMock()
    mock_context.path_exists.side_effect = lambda p: p in [
        "/boot/grub/grub.cfg",
        "/etc/default/grub",
        "/sys/firmware/efi",
    ]
    mock_context.find_executable_path.return_value = "/usr/bin/grub-install"
    mock_context.run_command.return_value = "/dev/sda1 on / type zfs (rw,relatime)"
    mock_context.read_file.return_value = """
GRUB_TIMEOUT=10
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=saved
GRUB_DISABLE_OS_PROBER=false
GRUB_ENABLE_CRYPTODISK=y
GRUB_BACKGROUND="/boot/grub/background.png"
"""

    scanner = GrubScanner()
    ir = scanner.scan(mock_context)

    assert ir["enable"] is True
    assert ir["efiSupport"] is True
    assert ir["timeout"] == 10
    assert ir["timeoutStyle"] == "menu"
    assert ir["default"] == "saved"
    assert ir["zfsSupport"] is True
    assert ir["useOSProber"] is True
    assert ir["enableCryptodisk"] is True


def test_grub_scanner_bios():
    mock_context = unittest.mock.MagicMock()
    mock_context.path_exists.side_effect = lambda p: p in [
        "/boot/grub/grub.cfg",
        "/etc/default/grub",
    ]
    mock_context.find_executable_path.return_value = "/usr/bin/grub-install"
    mock_context.read_file.return_value = "GRUB_TIMEOUT=5"

    scanner = GrubScanner()
    ir = scanner.scan(mock_context)

    assert ir["enable"] is True
    assert ir["efiSupport"] is False


def test_grub_mapper():
    mock_ir = {
        "enable": True,
        "efiSupport": True,
        "useOSProber": True,
        "enableCryptodisk": True,
    }

    mapper = GrubMapper()
    block = mapper.map(mock_ir)

    assert isinstance(block, SimpleOptionBlock)
    data = block.data["boot.loader.grub"]
    assert data["enable"] is True
    assert data["efiSupport"] is True
    assert data["useOSProber"] is True
    assert data["enableCryptodisk"] is True
