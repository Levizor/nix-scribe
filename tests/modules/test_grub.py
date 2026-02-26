from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import SimpleOptionBlock
from nix_scribe.modules.boot.loader.grub import GrubMapper, GrubScanner

MOCK_GRUB_DEFAULT = """
GRUB_TIMEOUT=10
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=saved
GRUB_DISABLE_OS_PROBER=false
GRUB_ENABLE_CRYPTODISK=y
GRUB_BACKGROUND="/boot/grub/background.png"
"""


def test_grub_scanner_efi(tmp_path, monkeypatch):
    (tmp_path / "etc/default").mkdir(parents=True)
    (tmp_path / "boot/grub").mkdir(parents=True)
    (tmp_path / "sys/firmware/efi").mkdir(parents=True)
    (tmp_path / "boot/grub/background.png").touch()
    (tmp_path / "boot/grub/grub.cfg").touch()
    (tmp_path / "bin").mkdir(parents=True)
    (tmp_path / "bin/grub-install").touch()
    (tmp_path / "etc/default/grub").write_text(MOCK_GRUB_DEFAULT)

    context = SystemContext(tmp_path)

    monkeypatch.setattr(
        context,
        "run_command",
        lambda cmd: "/dev/sda1 on / type zfs (rw,relatime)" if cmd == ["mount"] else "",
    )

    scanner = GrubScanner()
    ir = scanner.scan(context)

    assert ir["enable"] is True
    assert ir["efiSupport"] is True
    assert ir["timeout"] == 10
    assert ir["timeoutStyle"] == "menu"
    assert ir["default"] == "saved"
    assert ir["zfsSupport"] is True
    assert ir["useOSProber"] is True
    assert ir["enableCryptodisk"] is True
    assert ir["splashImage"] == "/boot/grub/background.png"


def test_grub_scanner_bios(tmp_path, monkeypatch):
    (tmp_path / "etc/default").mkdir(parents=True)
    (tmp_path / "boot/grub").mkdir(parents=True)
    (tmp_path / "boot/grub/grub.cfg").touch()
    (tmp_path / "etc/default/grub").write_text("GRUB_TIMEOUT=5")

    context = SystemContext(tmp_path)
    monkeypatch.setattr(
        context, "find_executable_path", lambda x: "/usr/bin/grub-install"
    )

    scanner = GrubScanner()
    ir = scanner.scan(context)

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
