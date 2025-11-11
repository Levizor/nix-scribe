import pytest

from writer.syntax_builder import NixSyntaxBuilder
from writer.value import nix_with, raw, to_nix


@pytest.fixture()
def writer():
    return NixSyntaxBuilder()


def test_write_nix_block(writer: NixSyntaxBuilder):
    data = {
        "networking": {"NetworkManager.enable": True, "firewall.enable": True},
        "security": {"sudo": {"wheelNeedsPassword": False}},
        "environment.systemPackages": nix_with("pkgs", ["vim", "curl"]),
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

"""
    )


def test_to_nix_conversion():
    assert to_nix(True) == "true"
    assert to_nix(False) == "false"
    assert to_nix(None) == "null"
    assert to_nix(123) == "123"
    assert to_nix(1.23) == "1.23"
    assert to_nix("hello") == '"hello"'
    assert to_nix(raw("pkgs.vim")) == "pkgs.vim"


def test_write_attr_simple_values(writer: NixSyntaxBuilder):
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


def test_write_dict_empty(writer: NixSyntaxBuilder):
    writer.write_dict({})
    nix_text = writer.gettext()
    print(nix_text)
    assert nix_text == ""


@pytest.mark.xfail
def test_write_function(writer: NixSyntaxBuilder):
    writer.write_function("my_function", ["pkgs", "lib"], {"package": "pkgs.hello"})
    nix_text = writer.gettext()
    print(nix_text)
    assert (
        nix_text
        == """\
my_function = { pkgs, lib }: {
  package = pkgs.hello;
};
"""
    )


@pytest.mark.xfail
def test_write_imports(writer: NixSyntaxBuilder):
    writer.add_import("./my-module.nix")
    writer.add_import("<nixpkgs>")
    nix_text = writer.gettext()
    print(nix_text)
    assert (
        nix_text
        == """\
imports = [
  ./my-module.nix
  <nixpkgs>
];
"""
    )
