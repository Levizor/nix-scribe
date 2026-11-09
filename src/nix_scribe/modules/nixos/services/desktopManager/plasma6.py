from __future__ import annotations

from nix_scribe.lib.nix_module import NixModule, option

PLASMA6_PACKAGES: set[str] = {
    # Core Plasma parts
    "kdePackages.plasma-desktop",
    "kdePackages.plasma-workspace",
    "kdePackages.kwin",
    "kdePackages.systemsettings",
    "kdePackages.kscreen",
    "kdePackages.kscreenlocker",
    "kdePackages.kactivitymanagerd",
    "kdePackages.kde-cli-tools",
    "kdePackages.kglobalacceld",
    "kdePackages.kwrited",
    "kdePackages.baloo",
    "kdePackages.milou",
    "kdePackages.kdegraphics-thumbnailers",
    "kdePackages.polkit-kde-agent-1",
    "kdePackages.drkonqi",
    "kdePackages.kde-inotify-survey",
    "kdePackages.libplasma",
    "kdePackages.plasma-integration",
    "kdePackages.kde-gtk-config",
    "kdePackages.breeze",
    "kdePackages.breeze-icons",
    "kdePackages.breeze-gtk",
    "kdePackages.ocean-sound-theme",
    "kdePackages.qqc2-breeze-style",
    "kdePackages.qqc2-desktop-style",
    "kdePackages.kdeplasma-addons",
    "kdePackages.kmenuedit",
    "kdePackages.kinfocenter",
    "kdePackages.plasma-systemmonitor",
    "kdePackages.ksystemstats",
    "kdePackages.libksysguard",
    "kdePackages.kcmutils",
    # Optional/standard Plasma utilities and apps
    "kdePackages.aurorae",
    "kdePackages.plasma-browser-integration",
    "kdePackages.plasma-workspace-wallpapers",
    "kdePackages.konsole",
    "kdePackages.ark",
    "kdePackages.elisa",
    "kdePackages.gwenview",
    "kdePackages.okular",
    "kdePackages.kate",
    "kdePackages.ktexteditor",
    "kdePackages.khelpcenter",
    "kdePackages.dolphin",
    "kdePackages.baloo-widgets",
    "kdePackages.dolphin-plugins",
    "kdePackages.spectacle",
    "kdePackages.ffmpegthumbs",
    "kdePackages.krdp",
    "kdePackages.kconfig",
    "kdePackages.plasma-keyboard",
    "kdePackages.kwallet",
    "kdePackages.kwalletmanager",
    "kdePackages.powerdevil",
    "kdePackages.bluedevil",
    "kdePackages.plasma-nm",
    "kdePackages.plasma-pa",
    "kdePackages.discover",
    "kdePackages.xdg-desktop-portal-kde",
}


class Plasma6(
    NixModule,
    prefix="services.desktopManager.plasma6",
    claims=PLASMA6_PACKAGES,
):
    """KDE Plasma 6 Desktop Environment"""

    enable: bool = option(default=False)
