from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pkgmap.schema import PackageResolution

from nix_scribe.lib.packages.models import DiscoveredPackage, InstallReason
from nix_scribe.lib.packages.pkgmap_resolver import PkgmapPackageResolver


def test_resolve_single_package(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_resolve(
        package: str,
        from_repo: str | None = None,
        to_repo: str | None = None,
        db_path: Path | str | None = None,
    ) -> PackageResolution | None:
        assert from_repo == "debian"
        assert to_repo == "nixpkgs"
        if package == "batcat":
            return PackageResolution(
                name="bat", version="0.24.0", repo="nix_unstable", repo_family="nix"
            )
        return None

    monkeypatch.setattr("pkgmap.resolve", mock_resolve)

    resolver = PkgmapPackageResolver()
    pkg = DiscoveredPackage(
        name="batcat", repository="debian", reason=InstallReason.EXPLICIT
    )

    resolved = resolver.resolve(pkg)

    assert resolved is not None
    assert resolved.name == "bat"
    assert resolved.original == pkg
    assert resolved.repository == "debian"
    assert resolved.is_explicit


def test_resolve_package_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pkgmap.resolve", lambda **kwargs: None)

    resolver = PkgmapPackageResolver()
    pkg = DiscoveredPackage(name="nonexistent-app", repository="debian")

    resolved = resolver.resolve(pkg)

    assert resolved is None


def test_resolve_many_mixed_repositories(monkeypatch: pytest.MonkeyPatch) -> None:
    batch_calls: list[tuple[tuple[str, ...], str | None, str | None, Any]] = []

    def mock_resolve_batch(
        packages: list[str],
        from_repo: str | None = None,
        to_repo: str | None = None,
        db_path: Path | str | None = None,
    ) -> dict[str, PackageResolution | None]:
        batch_calls.append((tuple(packages), from_repo, to_repo, db_path))
        if from_repo == "debian":
            return {
                "batcat": PackageResolution(
                    name="bat",
                    version="0.24.0",
                    repo="nix_unstable",
                    repo_family="nix",
                ),
                "unknown-pkg": None,
                "fd-find": PackageResolution(
                    name="fd",
                    version="10.1.0",
                    repo="nix_unstable",
                    repo_family="nix",
                ),
            }
        elif from_repo == "arch":
            return {
                "ripgrep": PackageResolution(
                    name="ripgrep",
                    version="14.1.0",
                    repo="nix_unstable",
                    repo_family="nix",
                ),
                "missing-arch": None,
            }
        return {}

    monkeypatch.setattr("pkgmap.resolve_batch", mock_resolve_batch)

    resolver = PkgmapPackageResolver()
    packages = [
        DiscoveredPackage(name="batcat", repository="debian"),
        DiscoveredPackage(name="unknown-pkg", repository="debian"),
        DiscoveredPackage(name="ripgrep", repository="arch"),
        DiscoveredPackage(name="fd-find", repository="debian"),
        DiscoveredPackage(name="missing-arch", repository="arch"),
    ]

    resolved, unmapped = resolver.resolve_many(packages)

    assert len(batch_calls) == 2
    assert batch_calls[0] == (
        ("batcat", "unknown-pkg", "fd-find"),
        "debian",
        "nixpkgs",
        None,
    )
    assert batch_calls[1] == (
        ("ripgrep", "missing-arch"),
        "arch",
        "nixpkgs",
        None,
    )

    assert [p.name for p in resolved] == ["bat", "ripgrep", "fd"]
    assert [p.original.name for p in resolved] == ["batcat", "ripgrep", "fd-find"]
    assert [p.name for p in unmapped] == ["unknown-pkg", "missing-arch"]


def test_resolve_many_empty() -> None:
    resolver = PkgmapPackageResolver()
    resolved, unmapped = resolver.resolve_many([])

    assert resolved == []
    assert unmapped == []


def test_resolver_custom_and_default_db_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom_path = tmp_path / "custom.db"
    captured_paths: list[Path | None] = []

    def mock_resolve(
        package: str,
        from_repo: str | None = None,
        to_repo: str | None = None,
        db_path: Path | str | None = None,
    ) -> PackageResolution | None:
        captured_paths.append(Path(db_path) if db_path else None)
        return PackageResolution(
            name="pkg", version="1.0", repo="nix_unstable", repo_family="nix"
        )

    monkeypatch.setattr("pkgmap.resolve", mock_resolve)

    resolver_custom = PkgmapPackageResolver(db_path=custom_path)
    assert resolver_custom.db_path == custom_path
    resolver_custom.resolve(DiscoveredPackage(name="test", repository="debian"))
    assert captured_paths[-1] == custom_path

    resolver_default = PkgmapPackageResolver()
    assert resolver_default.db_path is None
    resolver_default.resolve(DiscoveredPackage(name="test", repository="debian"))
    assert captured_paths[-1] is None
