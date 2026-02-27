import pytest

from nix_scribe.lib.asset import Asset
from nix_scribe.lib.nix_writer import NixWriter, nix_with, raw, with_pkgs


@pytest.fixture()
def writer():
    return NixWriter()


def test_write_nix_block(writer: NixWriter):
    data = {
        "networking": {"NetworkManager.enable": True, "firewall.enable": True},
        "security": {"sudo": {"wheelNeedsPassword": False}},
        "environment.systemPackages": nix_with("pkgs", [raw("vim"), raw("curl")]),
        "other.packages": with_pkgs("vim", "curl"),
    }

    writer.write_dict(data)
    nix_text = writer.gettext()

    assert (
        nix_text
        == """\
networking = {
  NetworkManager.enable = true;
  firewall.enable = true;
};

security = {
  sudo = {
    wheelNeedsPassword = false;
  };
};

environment.systemPackages = with pkgs; [
  vim
  curl
];

other.packages = with pkgs; [
  vim
  curl
];

"""
    )


def test_to_nix_conversion(writer: NixWriter):
    cases = {
        "true": True,
        "false": False,
        "null": None,
        "123": 123,
        "1.23": 1.23,
        '"hello"': "hello",
        "pkgs.vim": raw("pkgs.vim"),
        """''
  hello
  world
''""": "hello\nworld",
    }

    for key, value in cases.items():
        writer._write_value(value)
        assert key == writer.gettext()
        writer.clear()


def test_write_attr_simple_values(writer: NixWriter):
    writer.write_attr("key", "value")
    writer.write_attr("bool_key", True)
    writer["int_key"] = 123
    nix_text = writer.gettext()
    assert (
        nix_text
        == """\
key = "value";
bool_key = true;
int_key = 123;
"""
    )


def test_write_dict_empty(writer: NixWriter):
    writer.write_dict({})
    nix_text = writer.gettext()
    assert nix_text == ""


def test_write_attr_complex_keys(writer: NixWriter):
    cases = {
        "networking.networkmanager.enable": "networking.networkmanager.enable",
        "services.display-manager.enable": "services.display-manager.enable",
        'services."display-manager".enable': 'services."display-manager".enable',
        'settings."Greeter][Wallpaper][org.kde.image][General".Image': 'settings."Greeter][Wallpaper][org.kde.image][General".Image',
        '"123key"': '"123key"',
        'user."name.with.dots"': 'user."name.with.dots"',
        '"key with space"': "key with space",
        '"user@domain.com"': "user@domain.com",
        '"key:with:colon"': "key:with:colon",
        '"path/to/file"': "path/to/file",
        '"key\\"with\\"quotes"': 'key"with"quotes',
        '"fullyquoted"': '"fullyquoted"',
        '"key\\\\backslashes"': "key\\backslashes",
        '"::f"': "::f",
        '"127.0.0.1"': "127.0.0.1",
        '".hello"': ".hello",
        'a12."127"."0"."0"."1"': "a12.127.0.0.1",
        'a."12".c': "a.12.c",
    }

    for expected_key, input_key in cases.items():
        writer.write_attr(input_key, True)
        assert writer.gettext() == f"{expected_key} = true;\n"
        writer.clear()


def test_asset_rendering_and_collection(writer: NixWriter):
    asset = Asset("/src/path", "target.png")
    writer.write_attr("image", asset)

    assert writer.gettext() == "image = ./target.png;\n"
