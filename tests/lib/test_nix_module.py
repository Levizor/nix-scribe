from typing import Any

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.emitter import emit_nix_fragment
from nix_scribe.lib.nix_fragment import NixFragment, NixValue
from nix_scribe.lib.nix_module import (
    NixModule,
    OptionMetadata,
    get_option_metadata,
    option,
)
from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.nixfile import NixFile


class GitLfs(NixModule, claims={"git-lfs"}):
    enable: bool | None = option()
    enablePureSSHTransfer: bool | None = option()


class Git(NixModule, claims={"git"}, prefix="programs.git"):
    enable: bool | None = option()
    prompt_enable: bool | None = option("prompt.enable")
    config: dict[str, Any] = option()
    lfs: GitLfs | None = None


class Sudo(NixModule, claims={"sudo"}, prefix="security.sudo"):
    enable: bool | None = option()
    execWheelOnly: bool | None = option()
    wheelNeedsPassword: bool | None = option(
        comment="Allow wheel members to run sudo without password",
    )
    keepTerminfo: bool | None = option()
    extraConfig: str | None = option()


class UserEntry(NixModule):
    uid: int
    isNormalUser: bool | None = option()
    description: str | None = option()
    home: str | None = None
    group: str | None = option()
    extraGroups: list[str] = option()
    shell: Any = None


class Users(NixModule, prefix="users.users"):
    users: dict[str, UserEntry] = option(inline=True)
    bash_enable: bool | None = option(
        "programs.bash.enable",
        root=True,
        arguments={"pkgs"},
    )
    zsh_enable: bool | None = option(
        "programs.zsh.enable",
        root=True,
        arguments={"pkgs"},
    )


def test_nix_module_defaults_and_omission():
    sudo = Sudo(enable=True)
    assert sudo.to_dict() == {"enable": True}

    sudo_custom = Sudo(
        enable=True,
        execWheelOnly=True,
        wheelNeedsPassword=False,
        extraConfig="Defaults timestamp_timeout=15",
    )
    assert sudo_custom.to_dict() == {
        "enable": True,
        "execWheelOnly": True,
        "wheelNeedsPassword": False,
        "extraConfig": "Defaults timestamp_timeout=15",
    }


def test_nix_module_nested_and_claims():
    git_basic = Git(enable=True)
    assert git_basic.resolve_claims() == {"git"}
    assert git_basic.to_dict() == {"enable": True}

    git_full = Git(
        enable=True,
        prompt_enable=True,
        config={"user": {"name": "Alice"}},
        lfs=GitLfs(enable=True, enablePureSSHTransfer=True),
    )
    assert git_full.resolve_claims() == {"git", "git-lfs"}
    assert git_full.to_dict() == {
        "enable": True,
        "prompt.enable": True,
        "config": {"user": {"name": "Alice"}},
        "lfs": {
            "enable": True,
            "enablePureSSHTransfer": True,
        },
    }


def test_nix_module_field_level_claims():
    class Networking(NixModule, prefix="networking"):
        hostName: str | None = None
        useDHCP: bool | None = option(claims={"dhcpcd"})

    net_inactive = Networking(hostName="nixos")
    assert net_inactive.resolve_claims() == set()

    net_dhcp = Networking(hostName="nixos", useDHCP=True)
    assert net_dhcp.resolve_claims() == {"dhcpcd"}

    net_dhcp.claim("iproute2")
    assert net_dhcp.resolve_claims() == {"dhcpcd", "iproute2"}


def test_nix_module_assets_and_arguments():
    class Grub(NixModule, claims={"grub2"}, prefix="boot.loader.grub"):
        enable: bool | None = option()
        splashImage: Asset | None = None

    splash = Asset("grub-splash.png", b"PNGDATA")
    grub = Grub(enable=True, splashImage=splash)
    grub.add_asset(splash)
    grub.add_argument("pkgs")

    assert grub.resolve_assets() == {splash}

    fragment = grub.to_nix_fragment(
        name="grub",
        description="GRUB boot loader configuration.",
    )
    assert isinstance(fragment, NixFragment)
    assert fragment.name == "grub"
    assert fragment.arguments == {"pkgs"}
    assert fragment["boot.loader.grub"].value["splashImage"] == splash


def test_nix_module_inline_map_and_root_options():
    mod = Users(
        users={
            "alice": UserEntry(
                uid=1000,
                isNormalUser=True,
                description="Alice",
                home="/home/alice",
                group="alice",
                extraGroups=["wheel"],
                shell=raw("pkgs.bash"),
            )
        },
        bash_enable=True,
    )

    fragment = mod.to_nix_fragment(
        name="users",
        description="User accounts",
    )
    assert fragment.arguments == {"pkgs"}

    assert "users.users" in fragment.options
    assert "programs.bash.enable" in fragment.options
    assert "programs.zsh.enable" not in fragment.options
    assert fragment["users.users"]["alice"]["uid"] == 1000
    assert fragment["users.users"]["alice"]["isNormalUser"] is True
    assert fragment["programs.bash.enable"].value is True


def test_nix_module_comments_and_nixfile_rendering():
    sudo = Sudo(
        enable=True,
        wheelNeedsPassword=NixValue(False, "Detected in /etc/sudoers.d/wheel"),
    )
    fragment = sudo.to_nix_fragment(
        name="sudo",
        description="Sudo Configuration",
    )

    nix_file = NixFile("security")
    nix_file.add_fragment(fragment)
    rendered = nix_file.gettext()

    assert "# --- sudo: Sudo Configuration ---" in rendered
    assert "security.sudo.enable = true;" in rendered
    assert (
        "# Allow wheel members to run sudo without password | Detected in /etc/sudoers.d/wheel"
        in rendered
    )
    assert "security.sudo.wheelNeedsPassword = false;" in rendered


def test_mutable_default_isolation():
    u1 = UserEntry(uid=1000)
    u2 = UserEntry(uid=1001)

    assert u1.extraGroups == []
    assert u2.extraGroups == []
    assert u1.extraGroups is not u2.extraGroups

    u1.extraGroups.append("wheel")
    assert u1.extraGroups == ["wheel"]
    assert u2.extraGroups == []


def test_nix_module_subclass_inheritance():
    class BaseService(NixModule, claims={"base-daemon"}, arguments={"pkgs"}):
        enable: bool | None = option()

    class ExtendedService(BaseService, claims={"extra-tool"}, arguments={"lib"}):
        port: int | None = option()

    svc = ExtendedService(enable=True, port=9090)
    assert svc.resolve_claims() == {"base-daemon", "extra-tool"}
    frag = svc.to_nix_fragment(name="svc")
    assert frag.arguments == {"pkgs", "lib"}


def test_nix_module_nested_submodule_root_options():
    class Key(NixModule):
        key_id: str
        root_flag: bool | None = option(
            "security.globalFlag",
            root=True,
            arguments={"pkgs"},
        )

    class Auth(NixModule, prefix="services.auth"):
        enable: bool = True
        key: Key | None = None

    auth = Auth(enable=True, key=Key(key_id="k1", root_flag=True))
    frag = auth.to_nix_fragment()

    assert frag.arguments == {"pkgs"}
    assert "security.globalFlag" in frag
    assert frag["security.globalFlag"].value is True
    assert frag["services.auth"].value["key"]["key_id"] == "k1"


def test_nix_module_sets_and_tuples_serialization():
    class GroupPolicy(NixModule, prefix="security.policy"):
        allowed_users: set[str] = option()
        dimensions: tuple[int, ...] | None = option()

    policy = GroupPolicy(
        allowed_users={"alice", "bob"},
        dimensions=(1920, 1080),
    )
    data = policy.to_dict()
    assert isinstance(data["allowed_users"], list)
    assert set(data["allowed_users"]) == {"alice", "bob"}
    assert data["dimensions"] == [1920, 1080]


def test_nix_module_int_and_bool_type_safety():
    class Numeric(NixModule, prefix="metrics"):
        zero_val: int | None = option()
        false_val: bool | None = option()
        flag: bool | None = option()

    empty = Numeric()
    assert empty.to_dict() == {}

    populated = Numeric(zero_val=0, false_val=False, flag=True)
    assert populated.to_dict() == {
        "zero_val": 0,
        "false_val": False,
        "flag": True,
    }


def test_nix_fragment_container_dunders():
    frag = NixFragment(name="test", options={"a": NixValue(1), "b": NixValue(2)})
    assert bool(frag) is True
    assert "a" in frag
    assert "c" not in frag
    assert list(frag) == ["a", "b"]

    empty = NixFragment(name="empty")
    assert bool(empty) is False


def test_nix_module_option_metadata_and_helper():
    class Example(NixModule):
        flag: bool | None = option(
            "boot.test",
            comment="Static comment",
            claims={"test-pkg"},
            arguments={"pkgs"},
        )

    f = Example()._fields[0]
    meta = get_option_metadata(f)
    assert isinstance(meta, OptionMetadata)
    assert meta.path == "boot.test"
    assert meta.comment == "Static comment"
    assert meta.claims == {"test-pkg"}
    assert meta.arguments == {"pkgs"}


def test_nix_module_docstring_fallback_for_fragment():
    class DocstringService(NixModule, prefix="services.doc"):
        """Service description from docstring.

        Longer description that should be ignored for header.
        """

        enable: bool | None = option()

    svc = DocstringService(enable=True)
    frag = emit_nix_fragment(svc)
    assert frag.name == "doc"
    assert frag.description == "Service description from docstring."
    assert "services.doc" in frag

    custom_frag = emit_nix_fragment(
        svc, name="custom-doc", description="Explicit override"
    )
    assert custom_frag.name == "custom-doc"
    assert custom_frag.description == "Explicit override"


def test_nix_module_fields_property():
    class TestFields(NixModule):
        foo: str = "bar"
        count: int = 42

    mod = TestFields()
    f_names = [f.name for f in mod._fields]
    assert f_names == ["foo", "count"]


def test_nix_module_inferred_defaults_from_type_annotations():
    class Inferred(NixModule, prefix="test.inferred"):
        flag: bool = option()
        text: str = option()
        items: list[str] = option()
        mapping: dict[str, int] = option()
        tags: set[str] = option()
        nullable_text: str | None = option()
        nullable_list: list[str] | None = option()

    mod = Inferred()
    assert mod.flag is None
    assert mod.text is None
    assert mod.items == []
    assert mod.mapping == {}
    assert mod.tags == set()
    assert mod.nullable_text is None
    assert mod.nullable_list is None
    assert mod.to_dict() == {}

    # Ensure mutable defaults are isolated per instance
    mod.items.append("a")
    assert Inferred().items == []
