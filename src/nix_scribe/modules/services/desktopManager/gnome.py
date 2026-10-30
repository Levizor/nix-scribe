from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

gnome = Module("services.desktopManager.gnome")


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
    "gnome-tecla",
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
    "gnome-disk-utility",
    "seahorse",
    "sushi",
    "gnome-initial-setup",
    "gnome-remote-desktop",
    "gnome-user-share",
    "rygel",
    "gnome-browser-connector",
    "gnome-online-accounts",
}


@gnome.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {"enable": bool(context.find_executable_path("gnome-shell"))}


@gnome.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="gnome",
        description="Gnome desktop environment",
        data={"services.desktopManager.gnome": {"enable": True}},
        claims=GNOME_PACKAGES,
    )
