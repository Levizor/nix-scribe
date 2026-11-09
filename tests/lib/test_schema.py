from typing import Any

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.nix_writer import raw
from nix_scribe.lib.nixfile import NixFile
from nix_scribe.lib.option_block import NixFragment, NixValue
from nix_scribe.lib.schema import ModuleSchema, option


class GitLfsSchema(ModuleSchema, claims={"git-lfs"}):
    enable: bool = True
    enablePureSSHTransfer: bool = option(default=False)


class GitSchema(ModuleSchema, claims={"git"}, prefix="programs.git"):
    enable: bool = True
    prompt_enable: bool = option("prompt.enable", default=False)
    config: dict[str, Any] = option(default={})
    lfs: GitLfsSchema | None = None


class SudoSchema(ModuleSchema, claims={"sudo"}, prefix="security.sudo"):
    enable: bool = True
    execWheelOnly: bool = option(default=False)
    wheelNeedsPassword: bool = option(
        default=True,
        comment="Allow wheel members to run sudo without password",
    )
    keepTerminfo: bool = option(default=False)
    extraConfig: str = option(default="")


class UserEntrySchema(ModuleSchema):
    uid: int
    isNormalUser: bool = True
    description: str = option(default="")
    home: str | None = None
    group: str = option(default="users")
    extraGroups: list[str] = option(default=[])
    shell: Any = None


class UsersSchema(ModuleSchema, prefix="users.users"):
    users: dict[str, UserEntrySchema] = option(inline=True, default={})
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


def test_module_schema_defaults_and_omission():
    sudo = SudoSchema()
    assert sudo.to_dict() == {"enable": True}
    assert sudo.to_dict(keep_defaults=True) == {
        "enable": True,
        "execWheelOnly": False,
        "wheelNeedsPassword": True,
        "keepTerminfo": False,
        "extraConfig": "",
    }

    sudo_custom = SudoSchema(
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


def test_module_schema_keep_defaults_and_arguments():
    sudo = SudoSchema()
    fragment_default = sudo.to_nix_fragment(name="sudo")
    assert "wheelNeedsPassword" not in fragment_default["security.sudo"].value

    fragment_kept = sudo.to_nix_fragment(name="sudo", keep_defaults=True)
    assert fragment_kept["security.sudo"].value["wheelNeedsPassword"].value is True
    assert fragment_kept["security.sudo"].value["execWheelOnly"] is False

    users = UsersSchema()
    frag_default = users.to_nix_fragment()
    assert frag_default.arguments == set()
    frag_kept = users.to_nix_fragment(keep_defaults=True)
    assert frag_kept.arguments == {"pkgs"}


def test_module_schema_nested_and_claims():
    git_basic = GitSchema()
    assert git_basic.resolve_claims() == {"git"}
    assert git_basic.to_dict() == {"enable": True}

    git_full = GitSchema(
        prompt_enable=True,
        config={"user": {"name": "Alice"}},
        lfs=GitLfsSchema(enable=True, enablePureSSHTransfer=True),
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


def test_module_schema_field_level_claims():
    class NetworkingSchema(ModuleSchema, prefix="networking"):
        hostName: str | None = None
        useDHCP: bool = option(default=False, claims={"dhcpcd"})

    net_inactive = NetworkingSchema(hostName="nixos")
    assert net_inactive.resolve_claims() == set()

    net_dhcp = NetworkingSchema(hostName="nixos", useDHCP=True)
    assert net_dhcp.resolve_claims() == {"dhcpcd"}

    net_dhcp.claim("iproute2")
    assert net_dhcp.resolve_claims() == {"dhcpcd", "iproute2"}


def test_module_schema_assets_and_arguments():
    class GrubSchema(ModuleSchema, claims={"grub2"}, prefix="boot.loader.grub"):
        enable: bool = True
        splashImage: Asset | None = None

    splash = Asset("grub-splash.png", b"PNGDATA")
    grub = GrubSchema(splashImage=splash)
    grub.add_asset(splash)
    grub.add_argument("pkgs")

    assert grub.resolve_assets() == {splash}

    fragment = grub.to_nix_fragment(
        name="grub",
        description="GRUB Bootloader",
    )
    assert isinstance(fragment, NixFragment)
    assert fragment.name == "grub"
    assert fragment.description == "GRUB Bootloader"
    assert fragment.arguments == {"pkgs"}
    assert not hasattr(fragment, "assets")
    assert not hasattr(fragment, "claims")


def test_module_schema_inline_map_and_root_options():
    schema = UsersSchema(
        users={
            "alice": UserEntrySchema(
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

    fragment = schema.to_nix_fragment(
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


def test_module_schema_comments_and_nixfile_rendering():
    sudo = SudoSchema(
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
    u1 = UserEntrySchema(uid=1000)
    u2 = UserEntrySchema(uid=1001)

    assert u1.extraGroups == []
    assert u2.extraGroups == []
    assert u1.extraGroups is not u2.extraGroups

    u1.extraGroups.append("wheel")
    assert u1.extraGroups == ["wheel"]
    assert u2.extraGroups == []


def test_schema_subclass_inheritance():
    class BaseService(ModuleSchema, claims={"base-daemon"}, arguments={"pkgs"}):
        enable: bool = True

    class DerivedService(BaseService, claims={"derived-plugin"}, arguments={"lib"}):
        port: int = 8080

    svc = DerivedService()
    assert svc.resolve_claims() == {"base-daemon", "derived-plugin"}
    assert svc.to_nix_fragment().arguments == {"pkgs", "lib"}


def test_schema_nested_subschema_root_options():
    class KeySchema(ModuleSchema):
        id: str
        global_enable: bool = option("security.pki.enable", default=False, root=True)

    class AuthSchema(ModuleSchema, prefix="services.auth"):
        keys: list[KeySchema] = option(default=[])

    auth = AuthSchema(keys=[KeySchema(id="k1", global_enable=True)])
    fragment = auth.to_nix_fragment()

    assert "services.auth" in fragment
    assert "security.pki.enable" in fragment
    assert fragment["security.pki.enable"].value is True


def test_schema_sets_and_tuples_serialization():
    class GroupPolicySchema(ModuleSchema, prefix="security.policy"):
        trusted_groups: set[str] = option(default=set())
        ports: tuple[int, ...] = option(default=())

    policy = GroupPolicySchema(
        trusted_groups={"wheel", "admin"},
        ports=(80, 443),
    )
    fragment = policy.to_nix_fragment()
    file = NixFile("policy")
    file.add_fragment(fragment)
    text = file.gettext()

    assert "security.policy.trusted_groups = [" in text
    assert '"admin"' in text
    assert '"wheel"' in text
    assert "security.policy.ports = [" in text
    assert "80" in text
    assert "443" in text


def test_schema_int_and_bool_type_safety():
    class NumericSchema(ModuleSchema, prefix="metrics"):
        zero_val: int = option(default=0)
        false_val: bool = option(default=False)

    num_schema = NumericSchema(zero_val=0, false_val=False)
    assert num_schema.to_dict() == {}

    # 0 should NOT omit False, and False should NOT omit 0
    inverted = NumericSchema(zero_val=False, false_val=0)  # type: ignore[arg-type]
    res = inverted.to_dict()
    assert "zero_val" in res
    assert "false_val" in res


def test_nix_fragment_container_dunders():
    frag = NixFragment(name="test", options={"a": NixValue(1), "b": NixValue(2)})
    assert bool(frag) is True
    assert "a" in frag
    assert "c" not in frag
    assert list(frag) == ["a", "b"]

    empty = NixFragment(name="empty")
    assert bool(empty) is False


def test_option_metadata_dataclass():
    from dataclasses import fields

    from nix_scribe.lib.schema import OptionMetadata, get_option_metadata

    class ExampleSchema(ModuleSchema):
        plain_field: bool = True
        custom_opt: str = option(
            "custom.path",
            comment="Custom option comment",
            claims={"example-pkg"},
            arguments={"pkgs"},
            root=True,
            inline=False,
            omit_default=False,
        )

    f_map = {f.name: f for f in fields(ExampleSchema)}

    plain_meta = get_option_metadata(f_map["plain_field"])
    assert isinstance(plain_meta, OptionMetadata)
    assert plain_meta.path is None
    assert plain_meta.comment is None
    assert plain_meta.claims == set()
    assert plain_meta.omit_default is True

    custom_meta = get_option_metadata(f_map["custom_opt"])
    assert isinstance(custom_meta, OptionMetadata)
    assert custom_meta.path == "custom.path"
    assert custom_meta.comment == "Custom option comment"
    assert custom_meta.claims == {"example-pkg"}
    assert custom_meta.arguments == {"pkgs"}
    assert custom_meta.root is True
    assert custom_meta.omit_default is False


def test_emitter_direct_usage_and_docstring_fallback():
    from nix_scribe.lib.emitter import emit_dict, emit_nix_fragment

    class DocstringServiceSchema(ModuleSchema, prefix="services.doc"):
        """Service description from docstring."""

        enable: bool = True

    svc = DocstringServiceSchema()

    # Direct emit_dict
    assert emit_dict(svc) == {"enable": True}

    # Direct emit_nix_fragment with docstring fallback
    frag = emit_nix_fragment(svc)
    assert frag.name == "doc"
    assert frag.description == "Service description from docstring."
    assert "services.doc" in frag

    # Explicit override takes precedence
    custom_frag = emit_nix_fragment(
        svc, name="custom-doc", description="Explicit override"
    )
    assert custom_frag.name == "custom-doc"
    assert custom_frag.description == "Explicit override"


def test_schema_fields_property():
    class TestFieldsSchema(ModuleSchema):
        foo: str = "bar"
        count: int = 42

    schema = TestFieldsSchema()
    f_names = [f.name for f in schema._fields]
    assert f_names == ["foo", "count"]
