from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

plasma6 = Module("services.desktopManager.plasma6")


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
    "kdePackages.kwin-x11",
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
    "kdePackages.kcalc",
    "kdePackages.powerdevil",
    "kdePackages.bluedevil",
    "kdePackages.plasma-nm",
    "kdePackages.plasma-pa",
    "kdePackages.discover",
}


@plasma6.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {"enable": bool(context.find_executable_path("plasmashell"))}


@plasma6.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="plasma6",
        description="KDE Plasma 6 Desktop Environment",
        data={"services.desktopManager.plasma6": {"enable": True}},
        claims=PLASMA6_PACKAGES,
    )
