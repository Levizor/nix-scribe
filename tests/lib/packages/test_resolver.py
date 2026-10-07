import pytest

from nix_scribe.lib.packages import (
    DiscoveredPackage,
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


def test_package_resolver_abstract():
    with pytest.raises(TypeError):
        PackageResolver()


def test_package_resolver_resolve_many():
    resolver = MockPackageResolver(mapping={"known": "known"})

    resolved, unmapped = resolver.resolve_many(
        [
            DiscoveredPackage(name="known", repository="arch"),
            DiscoveredPackage(name="unknown", repository="arch"),
            DiscoveredPackage(name="other", repository="arch"),
        ]
    )
    assert len(resolved) == 1
    assert unmapped == [
        DiscoveredPackage(name="unknown", repository="arch"),
        DiscoveredPackage(name="other", repository="arch"),
    ]


def test_mock_package_resolver_mappings():
    mock = MockPackageResolver(
        mapping={
            ("debian", "batcat"): "bat",
            "explicit_resolved": ResolvedPackage(
                name="fd",
                original=DiscoveredPackage(name="fd-find", repository="debian"),
            ),
            "unmapped_tool": None,
        }
    )

    resolved = mock.resolve(DiscoveredPackage(name="batcat", repository="debian"))
    assert resolved is not None
    assert resolved.name == "bat"
    assert resolved.original_name == "batcat"
    assert resolved.repository == "debian"

    explicit = mock.resolve(
        DiscoveredPackage(name="explicit_resolved", repository="debian")
    )
    assert explicit == ResolvedPackage(
        name="fd", original=DiscoveredPackage(name="fd-find", repository="debian")
    )

    assert (
        mock.resolve(DiscoveredPackage(name="unmapped_tool", repository="debian"))
        is None
    )
    assert (
        mock.resolve(DiscoveredPackage(name="not_in_mapping", repository="debian"))
        is None
    )

    mock.add_mapping("new_tool", "canonical_tool", repository="arch")
    new_resolved = mock.resolve(DiscoveredPackage(name="new_tool", repository="arch"))
    assert new_resolved == ResolvedPackage(
        name="canonical_tool",
        original=DiscoveredPackage(name="new_tool", repository="arch"),
    )


def test_provider_injection():
    default_resolver = get_package_resolver()
    pkg = DiscoveredPackage(name="ripgrep", repository="arch")
    assert default_resolver.resolve(pkg) == ResolvedPackage(
        name="ripgrep", original=pkg
    )

    mock = MockPackageResolver({"zsh": "zsh"})
    set_package_resolver(mock)
    assert get_package_resolver() is mock

    set_package_resolver(None)
    resolver = get_package_resolver()
    assert resolver.resolve(pkg) == ResolvedPackage(name="ripgrep", original=pkg)
