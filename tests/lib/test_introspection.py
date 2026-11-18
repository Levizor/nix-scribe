from typing import Any

from nix_scribe.lib.introspection import discover_contracts, inspect_contract
from nix_scribe.lib.nix_module import NixModule, option
from nix_scribe.lib.nixpkgs_data import NixpkgsOptionsIndex, NixpkgsPackagesIndex


def test_inspect_contract_flat_and_nested() -> None:
    class Child(NixModule, claims={"child-pkg"}):
        enabled: bool = option("enable")

    class Parent(NixModule, prefix="programs.demo", claims={"demo-pkg"}):
        enable: bool = option()
        custom_path: str = option("nested.key", claims={"extra-pkg"})
        root_opt: bool = option("services.demo.enable", root=True)
        child: Child = option()

    spec = inspect_contract(Parent)
    assert spec.prefix == "programs.demo"
    assert spec.option_paths == [
        "programs.demo.enable",
        "programs.demo.nested.key",
        "services.demo.enable",
        "programs.demo.child.enable",
    ]
    assert spec.package_claims == {"demo-pkg", "extra-pkg", "child-pkg"}


def test_inspect_contract_collections_and_inline() -> None:
    class SubRange(NixModule):
        startUid: int = option()
        count: int = option()

    class Entry(NixModule):
        uid: int = option()
        ranges: list[SubRange] = option()

    class Container(NixModule, prefix="users.users"):
        entries: dict[str, Entry] = option(inline=True)

    spec = inspect_contract(Container)
    assert spec.option_paths == [
        "users.users.<name>.uid",
        "users.users.<name>.ranges.*.startUid",
        "users.users.<name>.ranges.*.count",
    ]


def test_inspect_contract_dict_non_inline() -> None:
    class ServiceEntry(NixModule):
        enable: bool = option()

    class PamLike(NixModule, prefix="security.pam"):
        services: dict[str, ServiceEntry] = option()
        raw_map: dict[str, Any] = option()

    spec = inspect_contract(PamLike)
    assert spec.option_paths == [
        "security.pam.services.<name>.enable",
        "security.pam.raw_map",
    ]


def test_discover_contracts_finds_all_modules() -> None:
    contracts = discover_contracts()
    prefixes = {cls.prefix for cls in contracts}
    assert "boot.loader.grub" in prefixes
    assert "networking" in prefixes
    assert "programs.git" in prefixes
    assert "security.sudo" in prefixes
    assert "services.openssh" in prefixes
    assert "users.users" in prefixes
    assert "virtualisation.vmVariant" in prefixes


def test_nixpkgs_options_index_lookup_and_submodule_fallback() -> None:
    index = NixpkgsOptionsIndex(
        {
            "programs.git.enable": {"type": "boolean"},
            "users.users.<name>.uid": {"type": "signed integer"},
            "virtualisation.vmVariant": {"type": "submodule"},
            "virtualisation.cores": {"type": "signed integer"},
        }
    )
    assert index.has_option("programs.git.enable") is True
    assert index.has_option("users.users.<name>.uid") is True
    assert index.has_option("virtualisation.vmVariant.virtualisation.cores") is True
    assert index.has_option("programs.git.nonexistent") is False
    assert index.has_option("virtualisation.vmVariant.virtualisation.fake") is False


def test_nixpkgs_packages_index_lookup() -> None:
    index = NixpkgsPackagesIndex({"git": {}, "kdePackages.sddm": {}})
    assert index.has_package("git") is True
    assert index.has_package("kdePackages.sddm") is True
    assert index.has_package("missing-pkg") is False
