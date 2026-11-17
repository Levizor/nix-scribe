from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option

GNOME_PACKAGES: set[str] = {
    # Core shell & session
    "gnome-shell",
    "gnome-session",
    "gnome-control-center",
    "gnome-settings-daemon",
    "gnome-backgrounds",
    "gnome-bluetooth",
    "gnome-color-manager",
    "gnome-tour",
    "gnome-user-docs",
    "gnome-menus",
    "glycin-thumbnailer",
    "gst-thumbnailers",
    # Core apps (services.gnome.core-apps)
    "baobab",
    "decibels",
    "epiphany",
    "gnome-text-editor",
    "gnome-calculator",
    "gnome-calendar",
    "gnome-characters",
    "gnome-clocks",
    "gnome-console",
    "gnome-contacts",
    "gnome-font-viewer",
    "gnome-logs",
    "gnome-maps",
    "gnome-music",
    "gnome-system-monitor",
    "tecla",
    "gnome-weather",
    "loupe",
    "nautilus",
    "papers",
    "gnome-connections",
    "showtime",
    "simple-scan",
    "snapshot",
    "yelp",
    # Default tools & services
    "adwaita-icon-theme",
    "gnome-disk-utility",
    "gnome-keyring",
    "seahorse",
    "sushi",
    "gnome-initial-setup",
    "gnome-remote-desktop",
    "gnome-user-share",
    "rygel",
    "gnome-browser-connector",
    "gnome-online-accounts",
    "xdg-desktop-portal-gnome",
}


class Gnome(
    NixModule,
    prefix="services.desktopManager.gnome",
    claims=GNOME_PACKAGES,
):
    """Gnome desktop environment"""

    enable: bool = option()
