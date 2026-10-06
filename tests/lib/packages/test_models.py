from dataclasses import FrozenInstanceError

import pytest

from nix_scribe.lib.packages import (
    DiscoveredPackage,
    InstallReason,
    PackageState,
    ResolvedPackage,
)


def test_discovered_package():
    pkg = DiscoveredPackage(name="ripgrep", repository="arch")
    assert pkg.name == "ripgrep"
    assert pkg.repository == "arch"

    with pytest.raises(FrozenInstanceError):
        pkg.name = "other"


def test_resolved_package_attributes():
    discovered = DiscoveredPackage(name="ripgrep", repository="arch")
    pkg = ResolvedPackage(name="ripgrep", original=discovered)
    assert pkg.name == "ripgrep"
    assert pkg.original == discovered
    assert pkg.original_name == "ripgrep"
    assert pkg.repository == "arch"
    assert pkg.category is None

    chrome_discovered = DiscoveredPackage(
        name="google-chrome-stable", repository="debian"
    )
    foreign_pkg = ResolvedPackage(
        name="google-chrome",
        original=chrome_discovered,
        category="web",
    )
    assert foreign_pkg.name == "google-chrome"
    assert foreign_pkg.original == chrome_discovered
    assert foreign_pkg.original_name == "google-chrome-stable"
    assert foreign_pkg.repository == "debian"
    assert foreign_pkg.category == "web"


def test_resolved_package_frozen():
    discovered = DiscoveredPackage(name="batcat", repository="debian")
    pkg = ResolvedPackage(name="bat", original=discovered)
    with pytest.raises(FrozenInstanceError):
        pkg.name = "something-else"


def test_package_state_query_and_claim():
    bat = ResolvedPackage(
        name="bat", original=DiscoveredPackage(name="batcat", repository="debian")
    )
    font = ResolvedPackage(
        name="fira-code",
        original=DiscoveredPackage(name="fonts-firacode", repository="debian"),
        category="fonts",
    )
    rg = ResolvedPackage(
        name="ripgrep",
        original=DiscoveredPackage(name="ripgrep", repository="arch"),
    )

    state = PackageState(
        packages=[bat, font, rg],
        unmapped=["internal-tool"],
    )

    assert state.unmapped == ["internal-tool"]
    assert state.resolved == [bat, font, rg]
    assert state.packages == [bat, font, rg]
    assert state.has("bat")
    assert state.has("fira-code")
    assert not state.has("unknown")

    assert state.get_by_category("fonts") == [font]
    assert state.get_by_category("nonexistent") == []

    assert not state.is_claimed("bat")
    assert state.claimed == set()
    assert state.unclaimed == [bat, font, rg]

    assert state.claim("bat") is True
    assert state.is_claimed("bat")
    assert state.claimed == {"bat"}

    assert state.claim("nonexistent") is False
    assert not state.is_claimed("nonexistent")

    unclaimed = state.get_unclaimed()
    assert unclaimed == [font, rg]
    assert state.unclaimed == [font, rg]


def test_package_state_empty():
    state = PackageState.empty()
    assert state.resolved == []
    assert state.packages == []
    assert state.unmapped == []
    assert state.claimed == set()
    assert state.unclaimed == []
    assert state.get_unclaimed() == []


def test_package_install_reasons():
    dep = DiscoveredPackage("libssl3", "debian", reason=InstallReason.DEPENDENCY)
    pre = DiscoveredPackage("curl", "debian", reason=InstallReason.PREINSTALLED)
    exp = DiscoveredPackage("ripgrep", "arch", reason=InstallReason.EXPLICIT)

    assert dep.is_dependency is True
    assert dep.is_explicit is False
    assert dep.is_preinstalled is False

    assert pre.is_preinstalled is True
    assert exp.is_explicit is True

    res_dep = ResolvedPackage("openssl", dep)
    res_pre = ResolvedPackage("curl", pre)
    res_exp = ResolvedPackage("ripgrep", exp)

    assert res_dep.is_dependency is True
    assert res_pre.is_preinstalled is True
    assert res_exp.is_explicit is True

    state = PackageState(packages=[res_dep, res_pre, res_exp])
    assert state.has("openssl")
    assert state.has("curl")
    assert state.has("ripgrep")

    assert state.unclaimed == [res_dep, res_pre, res_exp]
