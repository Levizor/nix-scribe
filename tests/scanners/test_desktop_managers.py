from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import NixFragment
from nix_scribe.scanners.services.desktopManager.cosmic import (
    COSMIC_PACKAGES,
    cosmic,
)
from nix_scribe.scanners.services.desktopManager.gnome import (
    GNOME_PACKAGES,
    gnome,
)
from nix_scribe.scanners.services.desktopManager.plasma6 import (
    PLASMA6_PACKAGES,
    plasma6,
)


def test_gnome_scanner(tmp_path):
    assert gnome.scan
    context = SystemContext(tmp_path)

    # Disabled when executable not present
    assert gnome.scan(context) is None

    # Enabled when executable is present in filesystem
    bin_dir = tmp_path / "usr/bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "gnome-shell").touch()
    mod = gnome.scan(context)
    assert mod is not None
    assert mod.enable is True

    block = mod.to_nix_fragment()
    assert isinstance(block, NixFragment)
    assert block["services.desktopManager.gnome"]["enable"] is True
    assert mod.resolve_claims() == GNOME_PACKAGES
    assert "nautilus" in mod.resolve_claims()
    assert "gnome-shell" in mod.resolve_claims()
    assert "xdg-desktop-portal-gnome" in mod.resolve_claims()
    assert "gnome-keyring" in mod.resolve_claims()


def test_plasma6_scanner(tmp_path):
    assert plasma6.scan
    context = SystemContext(tmp_path)

    # Disabled when executable not present
    assert plasma6.scan(context) is None

    # Enabled when executable is present in filesystem
    bin_dir = tmp_path / "usr/bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "plasmashell").touch()
    mod = plasma6.scan(context)
    assert mod is not None
    assert mod.enable is True

    block = mod.to_nix_fragment()
    assert isinstance(block, NixFragment)
    assert block["services.desktopManager.plasma6"]["enable"] is True
    assert mod.resolve_claims() == PLASMA6_PACKAGES
    assert "kdePackages.dolphin" in mod.resolve_claims()
    assert "kdePackages.plasma-desktop" in mod.resolve_claims()
    assert "kdePackages.xdg-desktop-portal-kde" in mod.resolve_claims()
    assert "kdePackages.kcalc" not in mod.resolve_claims()
    assert "kdePackages.kwin-x11" not in mod.resolve_claims()


def test_cosmic_scanner(tmp_path):
    assert cosmic.scan
    context = SystemContext(tmp_path)

    # Disabled when executable not present
    assert cosmic.scan(context) is None

    # Enabled when executable is present in filesystem
    bin_dir = tmp_path / "usr/bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "cosmic-session").touch()
    mod = cosmic.scan(context)
    assert mod is not None
    assert mod.enable is True

    block = mod.to_nix_fragment()
    assert isinstance(block, NixFragment)
    assert block["services.desktopManager.cosmic"]["enable"] is True
    assert mod.resolve_claims() == COSMIC_PACKAGES
    assert "cosmic-session" in mod.resolve_claims()
    assert "cosmic-files" in mod.resolve_claims()
    assert "xdg-desktop-portal-cosmic" in mod.resolve_claims()
    assert "cosmic-store" not in mod.resolve_claims()
