from dataclasses import FrozenInstanceError

import pytest

from nix_scribe.lib.packages import (
    DiscoveredPackage,
    PackageState,
    ResolvedPackage,
)


def test_discovered_package():
    pkg = DiscoveredPackage(name="ripgrep", distro="arch")
    assert pkg.name == "ripgrep"
    assert pkg.distro == "arch"

    with pytest.raises(FrozenInstanceError):
        pkg.name = "other"


def test_resolved_package_attributes():
    pkg = ResolvedPackage(name="ripgrep", original_name="ripgrep")
    assert pkg.name == "ripgrep"
    assert pkg.original_name == "ripgrep"
    assert pkg.repository is None
    assert pkg.category is None

    foreign_pkg = ResolvedPackage(
        name="google-chrome",
        original_name="google-chrome-stable",
        repository="google-chrome",
        category="web",
    )
    assert foreign_pkg.name == "google-chrome"
    assert foreign_pkg.original_name == "google-chrome-stable"
    assert foreign_pkg.repository == "google-chrome"
    assert foreign_pkg.category == "web"


def test_resolved_package_frozen():
    pkg = ResolvedPackage(name="bat", original_name="batcat")
    with pytest.raises(FrozenInstanceError):
        pkg.name = "something-else"


def test_package_state_query_and_claim():
    bat = ResolvedPackage(name="bat", original_name="batcat", repository="debian")
    font = ResolvedPackage(
        name="fira-code",
        original_name="fonts-firacode",
        repository="debian",
        category="fonts",
    )
    rg = ResolvedPackage(name="ripgrep", original_name="ripgrep", repository="debian")

    state = PackageState(
        packages=[bat, font, rg],
        unmapped=["internal-tool"],
    )

    assert state.unmapped == ["internal-tool"]
    assert state.has("bat")
    assert state.has("fira-code")
    assert not state.has("unknown")

    assert state.get_by_category("fonts") == [font]
    assert state.get_by_category("nonexistent") == []

    assert not state.is_claimed("bat")
    assert state.claim("bat") is True
    assert state.is_claimed("bat")

    assert state.claim("nonexistent") is False
    assert not state.is_claimed("nonexistent")

    unclaimed = state.get_unclaimed()
    assert unclaimed == [font, rg]


def test_package_state_empty():
    state = PackageState.empty()
    assert state.packages == []
    assert state.unmapped == []
    assert state.get_unclaimed() == []
