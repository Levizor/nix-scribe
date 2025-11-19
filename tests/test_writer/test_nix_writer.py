import pytest

from writer.nix_writer import NixWriter, nix_with, raw, with_pkgs


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
        print(writer.gettext())
        assert key == writer.gettext()
        writer.clear()


def test_write_attr_simple_values(writer: NixWriter):
    writer.write_attr("key", "value")
    writer.write_attr("bool_key", True)
    writer["int_key"] = 123
    nix_text = writer.gettext()
    print(nix_text)
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
    print(nix_text)
    assert nix_text == ""
