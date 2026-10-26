from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.modules.services.desktopManager.cosmic import (
    COSMIC_PACKAGES,
    cosmic,
)
from nix_scribe.modules.services.desktopManager.gnome import (
    GNOME_PACKAGES,
    gnome,
)
from nix_scribe.modules.services.desktopManager.plasma6 import (
    PLASMA6_PACKAGES,
    plasma6,
)


def test_gnome_scanner(tmp_path, monkeypatch):
    assert gnome.scan
    context = SystemContext(tmp_path)

    monkeypatch.setattr(
        context,
        "find_executable_path",
        lambda x: "/usr/bin/gnome-shell" if x == "gnome-shell" else None,
    )
    ir = gnome.scan(context)
    assert ir["enable"] is True

    monkeypatch.setattr(context, "find_executable_path", lambda _: None)
    ir_disabled = gnome.scan(context)
    assert ir_disabled["enable"] is False


def test_gnome_mapper():
    assert gnome.map
    assert gnome.map({"enable": False}) is None

    block = gnome.map({"enable": True})
    assert isinstance(block, ConfigFragment)
    assert block["services.desktopManager.gnome"]["enable"] is True
    assert block.claims == GNOME_PACKAGES
    assert "nautilus" in block.claims
    assert "gnome-shell" in block.claims


def test_plasma6_scanner(tmp_path, monkeypatch):
    assert plasma6.scan
    context = SystemContext(tmp_path)

    monkeypatch.setattr(
        context,
        "find_executable_path",
        lambda x: "/usr/bin/plasmashell" if x == "plasmashell" else None,
    )
    ir = plasma6.scan(context)
    assert ir["enable"] is True

    monkeypatch.setattr(context, "find_executable_path", lambda _: None)
    ir_disabled = plasma6.scan(context)
    assert ir_disabled["enable"] is False


def test_plasma6_mapper():
    assert plasma6.map
    assert plasma6.map({"enable": False}) is None

    block = plasma6.map({"enable": True})
    assert isinstance(block, ConfigFragment)
    assert block["services.desktopManager.plasma6"]["enable"] is True
    assert block.claims == PLASMA6_PACKAGES
    assert "kdePackages.dolphin" in block.claims
    assert "kdePackages.plasma-desktop" in block.claims


def test_cosmic_scanner(tmp_path, monkeypatch):
    assert cosmic.scan
    context = SystemContext(tmp_path)

    monkeypatch.setattr(
        context,
        "find_executable_path",
        lambda x: "/usr/bin/cosmic-session" if x == "cosmic-session" else None,
    )
    ir = cosmic.scan(context)
    assert ir["enable"] is True

    monkeypatch.setattr(context, "find_executable_path", lambda _: None)
    ir_disabled = cosmic.scan(context)
    assert ir_disabled["enable"] is False


def test_cosmic_mapper():
    assert cosmic.map
    assert cosmic.map({"enable": False}) is None

    block = cosmic.map({"enable": True})
    assert isinstance(block, ConfigFragment)
    assert block["services.desktopManager.cosmic"]["enable"] is True
    assert block.claims == COSMIC_PACKAGES
    assert "cosmic-session" in block.claims
    assert "cosmic-files" in block.claims
