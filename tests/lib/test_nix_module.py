from typing import Any

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.emitter import emit_nix_fragment
from nix_scribe.lib.nix_module import (
    NixModule,
    OptionMetadata,
    get_option_metadata,
    option,
)
from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import NixFragment, NixValue


class GitLfs(NixModule, claims={"git-lfs"}):
    enable: bool = True
    enablePureSSHTransfer: bool = option(default=False)


class Git(NixModule, claims={"git"}, prefix="programs.git"):
    enable: bool = True
    prompt_enable: bool = option("prompt.enable", default=False)
    config: dict[str, Any] = option(default={})
    lfs: GitLfs | None = None


class Sudo(NixModule, claims={"sudo"}, prefix="security.sudo"):
    enable: bool = True
    execWheelOnly: bool = option(default=False)
    wheelNeedsPassword: bool = option(
        default=True,
        comment="Allow wheel members to run sudo without password",
    )
    keepTerminfo: bool = option(default=False)
    extraConfig: str = option(default="")


class UserEntry(NixModule):
    uid: int
    isNormalUser: bool = True
    description: str = option(default="")
    home: str | None = None
    group: str = option(default="users")
    extraGroups: list[str] = option(default=[])
    shell: Any = None


class Users(NixModule, prefix="users.users"):
    users: dict[str, UserEntry] = option(inline=True, default={})
    bash_enable: bool = option(
        "programs.bash.enable",
        default=False,
        root=True,
        arguments={"pkgs"},
    )
    zsh_enable: bool = option(
        "programs.zsh.enable",
        default=False,
        root=True,
        arguments={"pkgs"},
    )


def test_nix_module_defaults_and_omission():
    sudo = Sudo()
    assert sudo.to_dict() == {"enable": True}
    assert sudo.to_dict(keep_defaults=True) == {
        "enable": True,
        "execWheelOnly": False,
        "wheelNeedsPassword": True,
        "keepTerminfo": False,
        "extraConfig": "",
    }

    sudo_custom = Sudo(
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


def test_nix_module_keep_defaults_and_arguments():
    sudo = Sudo()
    fragment_default = sudo.to_nix_fragment(name="sudo")
    assert "wheelNeedsPassword" not in fragment_default["security.sudo"].value

    fragment_kept = sudo.to_nix_fragment(name="sudo", keep_defaults=True)
    assert fragment_kept["security.sudo"].value["wheelNeedsPassword"].value is True
    assert fragment_kept["security.sudo"].value["execWheelOnly"] is False

    users = Users()
    frag_default = users.to_nix_fragment()
    assert frag_default.arguments == set()
    frag_kept = users.to_nix_fragment(keep_defaults=True)
    assert frag_kept.arguments == {"pkgs"}


def test_nix_module_nested_and_claims():
    git_basic = Git()
    assert git_basic.resolve_claims() == {"git"}
    assert git_basic.to_dict() == {"enable": True}

    git_full = Git(
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
        useDHCP: bool = option(default=False, claims={"dhcpcd"})

    net_inactive = Networking(hostName="nixos")
    assert net_inactive.resolve_claims() == set()

    net_dhcp = Networking(hostName="nixos", useDHCP=True)
    assert net_dhcp.resolve_claims() == {"dhcpcd"}

    net_dhcp.claim("iproute2")
    assert net_dhcp.resolve_claims() == {"dhcpcd", "iproute2"}


def test_nix_module_assets_and_arguments():
    class Grub(NixModule, claims={"grub2"}, prefix="boot.loader.grub"):
        enable: bool = True
        splashImage: Asset | None = None

    splash = Asset("grub-splash.png", b"PNGDATA")
    grub = Grub(splashImage=splash)
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
        enable: bool = True

    class ExtendedService(BaseService, claims={"extra-tool"}, arguments={"lib"}):
        port: int = option(default=8080)

    svc = ExtendedService(port=9090)
    assert svc.resolve_claims() == {"base-daemon", "extra-tool"}
    frag = svc.to_nix_fragment(name="svc")
    assert frag.arguments == {"pkgs", "lib"}


def test_nix_module_nested_submodule_root_options():
    class Key(NixModule):
        key_id: str
        root_flag: bool = option(
            "security.globalFlag",
            default=False,
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
        allowed_users: set[str] = option(default_factory=set)
        dimensions: tuple[int, ...] = option(default=())

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
        zero_val: int = option(default=0)
        false_val: bool = option(default=False)
        true_default: bool = option(default=True)

    num_mod = Numeric(zero_val=0, false_val=False, true_default=True)
    assert num_mod.to_dict() == {}

    # False set on true_default must be emitted
    disabled = Numeric(true_default=False)
    assert disabled.to_dict() == {"true_default": False}

    # 0 should NOT omit False, and False should NOT omit 0
    inverted = Numeric(zero_val=False, false_val=0)  # type: ignore[arg-type]
    res = inverted.to_dict()
    assert res == {"zero_val": False, "false_val": 0}


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
        flag: bool = option(
            "boot.test",
            default=True,
            comment="Static comment",
            claims={"test-pkg"},
            arguments={"pkgs"},
            omit_default=False,
        )

    f = Example()._fields[0]
    meta = get_option_metadata(f)
    assert isinstance(meta, OptionMetadata)
    assert meta.path == "boot.test"
    assert meta.comment == "Static comment"
    assert meta.claims == {"test-pkg"}
    assert meta.arguments == {"pkgs"}
    assert meta.omit_default is False
    assert meta.explicit_default is True


def test_nix_module_docstring_fallback_for_fragment():
    class DocstringService(NixModule, prefix="services.doc"):
        """Service description from docstring.

        Longer description that should be ignored for header.
        """

        enable: bool = True

    svc = DocstringService()
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
