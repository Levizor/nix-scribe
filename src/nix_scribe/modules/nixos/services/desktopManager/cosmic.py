from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option

COSMIC_PACKAGES: set[str] = {
    # Core packages
    "cosmic-applets",
    "cosmic-app-library",
    "cosmic-bg",
    "cosmic-comp",
    "cosmic-files",
    "cosmic-greeter",
    "cosmic-idle",
    "cosmic-initial-setup",
    "cosmic-launcher",
    "cosmic-notifications",
    "cosmic-osd",
    "cosmic-osk",
    "cosmic-panel",
    "cosmic-session",
    "cosmic-settings",
    "cosmic-settings-daemon",
    "cosmic-workspaces-epoch",
    # Default desktop apps and themes
    "cosmic-edit",
    "cosmic-icons",
    "cosmic-monitor",
    "cosmic-player",
    "cosmic-randr",
    "cosmic-reader",
    "cosmic-screenshot",
    "cosmic-term",
    "cosmic-viewer",
    "cosmic-wallpapers",
    "cosmic-sound-theme",
    "pop-icon-theme",
    "pop-launcher",
    "xdg-desktop-portal-cosmic",
}


class Cosmic(
    NixModule,
    prefix="services.desktopManager.cosmic",
    claims=COSMIC_PACKAGES,
):
    """Cosmic desktop environment"""

    enable: bool = option(default=False)
