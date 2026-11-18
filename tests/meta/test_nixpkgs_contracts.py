import os
import re
from pathlib import Path

import pytest

from nix_scribe.lib.introspection import discover_contracts, inspect_contract
from nix_scribe.lib.nix_module import NixModule
from nix_scribe.lib.nixpkgs_data import (
    DEFAULT_CHANNEL,
    NixpkgsOptionsIndex,
    NixpkgsPackagesIndex,
)


def _resolve_target_contracts() -> list[type[NixModule]]:
    """Resolves contracts lazily, limiting imports to requested files when specified."""
    raw_filter = os.environ.get("NIX_SCRIBE_META_MODULES", "").strip()
    if not raw_filter:
        return discover_contracts()

    tokens = [t for t in re.split(r"[\s,]+", raw_filter) if t]
    file_tokens = [t for t in tokens if t.endswith(".py") or Path(t).is_file()]
    name_tokens = [t for t in tokens if t not in file_tokens]

    contracts: list[type[NixModule]] = []
    if file_tokens:
        contracts.extend(discover_contracts(paths=file_tokens))
    if name_tokens:
        target_names = set(name_tokens)
        contracts.extend(
            cls
            for cls in discover_contracts()
            if (cls.prefix or cls.__name__) in target_names
            or cls.__module__ in target_names
        )

    return list(dict.fromkeys(contracts))


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "contract_cls" not in metafunc.fixturenames:
        return
    if metafunc.config.option.markexpr == "not meta":
        metafunc.parametrize("contract_cls", [])
        return

    contracts = _resolve_target_contracts()
    metafunc.parametrize(
        "contract_cls",
        contracts,
        ids=[cls.prefix or cls.__name__ for cls in contracts],
    )


@pytest.fixture(scope="session")
def options_index() -> NixpkgsOptionsIndex:
    channel = os.environ.get("NIX_SCRIBE_NIXPKGS_CHANNEL", DEFAULT_CHANNEL)
    force_refresh = os.environ.get("NIX_SCRIBE_FORCE_REFRESH") == "1"
    return NixpkgsOptionsIndex.from_channel(channel, force_refresh=force_refresh)


@pytest.fixture(scope="session")
def packages_index() -> NixpkgsPackagesIndex:
    channel = os.environ.get("NIX_SCRIBE_NIXPKGS_CHANNEL", DEFAULT_CHANNEL)
    force_refresh = os.environ.get("NIX_SCRIBE_FORCE_REFRESH") == "1"
    return NixpkgsPackagesIndex.from_channel(channel, force_refresh=force_refresh)


@pytest.mark.meta
def test_contract_against_nixpkgs(
    contract_cls: type[NixModule],
    options_index: NixpkgsOptionsIndex,
    packages_index: NixpkgsPackagesIndex,
) -> None:
    spec = inspect_contract(contract_cls)

    missing_options = [
        opt for opt in spec.option_paths if not options_index.has_option(opt)
    ]
    missing_packages = [
        pkg
        for pkg in sorted(spec.package_claims)
        if not packages_index.has_package(pkg)
    ]

    assert not missing_options, (
        f"[{contract_cls.__name__}] Options not found in nixpkgs: {missing_options}"
    )
    assert not missing_packages, (
        f"[{contract_cls.__name__}] Claimed packages not found in nixpkgs: {missing_packages}"
    )
