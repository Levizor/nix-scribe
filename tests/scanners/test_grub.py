from nix_scribe.lib.context import SystemContext
from nix_scribe.modules.nixos.boot.loader.grub import Grub
from nix_scribe.scanners.boot.loader.grub import grub

MOCK_GRUB_DEFAULT = """
GRUB_TIMEOUT=10
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=saved
GRUB_DISABLE_OS_PROBER=false
GRUB_ENABLE_CRYPTODISK=y
GRUB_BACKGROUND="/boot/grub/background.png"
"""


def test_grub_scanner_empty(tmp_path):
    context = SystemContext(tmp_path)
    assert grub.scan(context) is None


def test_grub_scanner_efi(tmp_path):
    assert grub.scan
    (tmp_path / "etc/default").mkdir(parents=True)
    (tmp_path / "boot/grub").mkdir(parents=True)
    (tmp_path / "sys/firmware/efi").mkdir(parents=True)
    (tmp_path / "boot/grub/background.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "boot/grub/grub.cfg").touch()
    (tmp_path / "bin").mkdir(parents=True)
    (tmp_path / "bin/grub-install").touch()
    (tmp_path / "etc/default/grub").write_text(MOCK_GRUB_DEFAULT)
    (tmp_path / "etc/fstab").write_text("/dev/sda1 / zfs defaults 0 0\n")

    context = SystemContext(tmp_path)
    mod = grub.scan(context)

    assert isinstance(mod, Grub)
    assert mod.enable is True
    assert mod.efiSupport is True
    assert mod.timeoutStyle == "menu"
    assert mod.default == "saved"
    assert mod.zfsSupport is True
    assert mod.useOSProber is True
    assert mod.enableCryptodisk is True
    assert mod.splashImage is not None
    assert str(mod.splashImage) == "./boot-loader-grub-background.png"
    assert mod.splashImage.content == b"\x89PNG\r\n\x1a\n"
    assert mod.resolve_claims() == {"grub2"}

    fragment = mod.to_nix_fragment()
    data = fragment["boot.loader.grub"].value
    assert data["enable"] is True
    assert data["efiSupport"] is True
    assert data["useOSProber"] is True
    assert data["enableCryptodisk"] is True
    assert str(data["splashImage"]) == "./boot-loader-grub-background.png"
    assert mod.splashImage in fragment.assets


def test_grub_scanner_bios(tmp_path, monkeypatch):
    assert grub.scan
    (tmp_path / "etc/default").mkdir(parents=True)
    (tmp_path / "boot/grub").mkdir(parents=True)
    (tmp_path / "boot/grub/grub.cfg").touch()
    (tmp_path / "etc/default/grub").write_text("GRUB_TIMEOUT=5")

    context = SystemContext(tmp_path)
    monkeypatch.setattr(
        context, "find_executable_path", lambda x: "/usr/bin/grub-install"
    )

    mod = grub.scan(context)

    assert isinstance(mod, Grub)
    assert mod.enable is True
    assert not mod.efiSupport
