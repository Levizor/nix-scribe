from dataclasses import FrozenInstanceError

import pytest

from nix_scribe.lib.package_resolver import (
    PackageResolver,
    ResolvedPackage,
    get_package_resolver,
    set_package_resolver,
)
from tests.mocks.mock_resolver import MockPackageResolver


@pytest.fixture(autouse=True)
def reset_resolver():
    yield
    set_package_resolver(None)


def test_resolved_package_attributes():
    pkg = ResolvedPackage(name="ripgrep", original_name="ripgrep")
    assert pkg.name == "ripgrep"
    assert pkg.original_name == "ripgrep"
    assert pkg.repository is None

    foreign_pkg = ResolvedPackage(
        name="google-chrome",
        original_name="google-chrome-stable",
        repository="google-chrome",
    )
    assert foreign_pkg.name == "google-chrome"
    assert foreign_pkg.original_name == "google-chrome-stable"
    assert foreign_pkg.repository == "google-chrome"


def test_resolved_package_frozen():
    pkg = ResolvedPackage(name="bat", original_name="batcat")
    with pytest.raises(FrozenInstanceError):
        pkg.name = "something-else"


def test_package_resolver_abstract():
    with pytest.raises(TypeError):
        PackageResolver()


def test_package_resolver_resolve_many():
    resolver = MockPackageResolver(mapping={"known": "known"}, distro="arch")
    assert resolver.distro == "arch"

    resolved, unmapped = resolver.resolve_many(["known", "unknown", "other"])
    assert len(resolved) == 1
    assert resolved[0].name == "known"
    assert unmapped == ["unknown", "other"]


def test_mock_package_resolver_mappings():
    mock = MockPackageResolver(
        mapping={
            "batcat": "bat",
            "explicit_resolved": ResolvedPackage(
                name="fd", original_name="fd-find", repository="debian"
            ),
            "unmapped_tool": None,
        },
        distro="debian",
    )
    assert mock.distro == "debian"

    resolved = mock.resolve("batcat")
    assert resolved is not None
    assert resolved.name == "bat"
    assert resolved.original_name == "batcat"
    assert resolved.repository is None

    explicit = mock.resolve("explicit_resolved")
    assert explicit == ResolvedPackage(
        name="fd", original_name="fd-find", repository="debian"
    )

    assert mock.resolve("unmapped_tool") is None
    assert mock.resolve("not_in_mapping") is None

    mock.add_mapping("new_tool", "canonical_tool", repository="repo")
    new_resolved = mock.resolve("new_tool")
    assert new_resolved == ResolvedPackage(
        name="canonical_tool", original_name="new_tool", repository="repo"
    )


def test_provider_injection():
    with pytest.raises(RuntimeError, match="No package resolver configured"):
        get_package_resolver()

    mock = MockPackageResolver({"zsh": "zsh"})
    set_package_resolver(mock)
    assert get_package_resolver() is mock

    set_package_resolver(None)
    with pytest.raises(RuntimeError, match="No package resolver configured"):
        get_package_resolver()
