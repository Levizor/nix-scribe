from typing import Any

from nix_scribe.lib.context import SystemContext
from nix_scribe.lib.option_block import ConfigFragment
from nix_scribe.lib.registry import Module

cosmic = Module("services.desktopManager.cosmic")


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
    "cosmic-wallpapers",
    "cosmic-sound-theme",
    "cosmic-store",
    "pop-icon-theme",
    "pop-launcher",
}


@cosmic.scanner()
def scan(context: SystemContext) -> dict[str, Any]:
    return {
        "enable": bool(
            context.find_executable_path("cosmic-session")
            or context.find_executable_path("cosmic-comp")
        )
    }


@cosmic.mapper()
def map(ir: dict[str, Any]) -> ConfigFragment | None:
    if not ir.get("enable"):
        return None

    return ConfigFragment(
        name="cosmic",
        description="Cosmic desktop environment",
        data={"services.desktopManager.cosmic": {"enable": True}},
        claims=COSMIC_PACKAGES,
    )
